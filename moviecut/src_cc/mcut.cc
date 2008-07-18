 /* Copyright (C) 2007, 2008 Anders Holst
  *
  * This program is free software; you can redistribute it and/or
  * modify it under the terms of the GNU General Public License as
  * published by the Free Software Foundation; either version 2, or
  * (at your option) any later version.
  * 
  * This program is distributed in the hope that it will be useful,
  * but WITHOUT ANY WARRANTY; without even the implied warranty of
  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  * GNU General Public License for more details.
  * 
  * You should have received a copy of the GNU General Public License
  * along with this software; see the file COPYING.  If not, write to
  * the Free Software Foundation, Inc., 59 Temple Place, Suite 330,
  * Boston, MA 02111-1307 USA
  */

#define _LARGEFILE64_SOURCE
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LEN 24064

static off64_t* buf0 = 0;
static off64_t* buf1 = 0;
static off64_t time_offset;
static off64_t size_offset;

int use_leadin = 1;
int use_leadout = 1;

inline int absless(long long int x, int lim)
{
  return (x<lim && x>-lim);
}

double strtotime(char* str)
{
  int i=0, t1, tt;
  char *p1, *p2;
  double tmp;
  p1 = str;
  tt = strtol(p1, &p2, 10);
  if (p1==p2) return -1.0;
  while (*p2 == ':' && i<2) {
    i++;
    if (p2-p1>2) return -1.0;
    p1 = p2+1;
    t1 = strtol(p1, &p2, 10);
    if (p1==p2) return -1.0;
    tt = 60*tt + t1;
  }
  if (i>0 && p2-p1>2) return -1.0;
  if (*p2 == 0) return (double)tt;
  if (*p2 != '.') return -1.0;
  p1 = p2+1;
  t1 = strtol(p1, &p2, 10);
  for (i=0, tmp=1.0; i<(p2-p1); tmp*=0.1, i++);
  return (double)tt + tmp*t1;
}

char* timetostr(double tm)
{
  static char buf[15];
  int r = (int)(tm/60);
  sprintf(buf, "%d:%d:%.3f", r/60, r%60, tm-60*r);
  return buf;
}

inline unsigned int byteswop(unsigned int n)
{
  return ((n&0xff000000)>>24) | ((n&0xff0000)>>8) | ((n&0xff00)<<8) | ((n&0xff)<<24);
}

inline unsigned long long int byteswopl(unsigned long long int n)
{
  return (n>>56) | ((n>>40)&0xff00) | ((n>>24)&0xff0000) | ((n>>8)&0xff000000) | ((n&0xff000000)<<8) | ((n&0xff0000)<<24) | ((n&0xff00)<<40) | ((n&0xff)<<56);
}

double inttotime(unsigned int t1, unsigned int t2)
{
  return (byteswop(t2)*1.1111111111111112e-05 + byteswop(t1)*47721.858844444447);
}

double lltotime(long long int t)
{
  return ((unsigned int)(t&0xffffffff)*1.1111111111111112e-05) + ((unsigned int)(t>>32)*47721.858844444447);
}

void timetoint(double tm, unsigned int& t1, unsigned int& t2)
{
  double tmp=tm/47721.858844444447;
  t1 = byteswop((unsigned int)tmp);
  t2 = byteswop((unsigned int)((tm - t1*47721.858844444447)*90000));
}

int readbufinternal(int f)
{
  off64_t* buf;
  buf = buf0;
  buf0 = buf1;
  buf1 = buf;
  if (read(f, buf, 16) != 16)
    return 0;
  buf[0] = (off64_t)byteswopl((unsigned long long int)buf[0]);
  buf[1] = (off64_t)byteswopl((unsigned long long int)buf[1]);
  return 1;
}

void writebufinternal(int f)
{
  off64_t buf2[2];
  buf2[0] = (off64_t)byteswopl((unsigned long long int)buf0[0] - size_offset);
  buf2[1] = (off64_t)byteswopl((unsigned long long int)buf0[1]);
  write(f, buf2, 16);
}

off64_t readoff(int f, int fo, double t, int beg, double& tr)
{
  static off64_t lastreturn;
  static double last;
  static int endp;
  off64_t sizetmp;
  double tt, lt;
  if (!buf0) {
    buf0 = new off64_t[2];
    buf1 = new off64_t[2];
    if (!(readbufinternal(f) && readbufinternal(f))) {
      printf("The corresponding \".ap\"-file is empty.\n");
      exit(8);
    }
    time_offset = buf0[1];
    if (buf1[1] > buf0[1] && buf1[1] - buf0[1] < 900000)
      time_offset -= (buf1[1]-buf0[1])*buf0[0]/(buf1[0]-buf0[0]);
    size_offset = buf0[0];
    lastreturn = 0;
    last = 0.0;
    endp = 0;
  }
  if (t < last && t != -1.0) {
    sizetmp = buf0[0];
    lseek(f, 0, SEEK_SET);
    readbufinternal(f);
    readbufinternal(f);
    time_offset = buf0[1];
    if (buf1[1]>buf0[1] && buf1[1]-buf0[1]<900000)
      time_offset -= (buf1[1]-buf0[1])*buf0[0]/(buf1[0]-buf0[0]);
    size_offset += buf0[0] - sizetmp;
    lastreturn = 0;
    last = 0.0;
    endp = 0;
  }
  if (t == last || endp == 1) {
    return lastreturn;
  }
  if (!beg)
    writebufinternal(fo);
  last = t;
  lt = lltotime(buf0[1] - time_offset);
  tt = lltotime(buf1[1] - time_offset);
  sizetmp = buf0[0];
  while (tt < t || t == -1.0) {
    if (!readbufinternal(f))
      endp = 1;
    if (!beg)
      writebufinternal(fo);
    if (endp)
      break;
    if (buf1[1] < buf0[1] || buf1[1] - buf0[1] > 900000) {
      if (absless(buf1[1] + ((long long int)1)<<33 - buf0[1], 900000))
	time_offset -= ((long long int)1)<<33;
      else
	time_offset += buf1[1] - buf0[1];
    }
    lt = tt;
    tt = lltotime(buf1[1] - time_offset);
  }
  if (endp) {
    tr = tt;
  } else if (beg ? (lt == tt || (t-lt > tt-t && tt-t<0.18)) : (t-lt >= tt-t || t-lt>0.18)) {
    if (!readbufinternal(f))
      endp = 1;
    if (!beg)
      writebufinternal(fo);
    tr = tt;
  } else {
    tr = lt;
  }
  if (beg)
    size_offset += buf0[0] - sizetmp;
  lastreturn = buf0[0];
  return lastreturn;
}

int framepid(char* buf, int pos)
{
  return ((buf[pos+1] & 0x1f) << 8) + buf[pos+2];
}

int framesearch_f(char* buf, int start, int stop, int pid)
{
  char* p;
  int pos = -1;
  for (p = buf+start; p < buf+stop-3; p++)
    if (p[0]==0 && p[1]==0 && p[2]==1 && p[3]==0) {
        pos = ((p - buf)/188)*188;
        if (pid == -1 || framepid(buf, pos) == pid)
          return pos;
    }
  return -1;
}

int framesearch_b(char* buf, int start, int stop, int pid)
{
  char* p;
  int pos = -1;
  for (p = buf+stop-1; p >= buf+start+3; p--)
    if (p[0]==0 && p[-1]==1 && p[-2]==0 && p[-3]==0) {
        pos = ((p - buf)/188)*188;
        if (pid == -1 || framepid(buf, pos) == pid)
          return pos;
    }
  return -1;
}

int transfer_start(int f_ts, int f_out, off64_t n1, off64_t& n1ret)
{
  off64_t num;
  int pos, tmp;
  char buf[LEN];
  if (use_leadin) {
    num = 0;
    tmp = 0;
    do {
      num += LEN;
      if (num > n1)
        tmp = LEN - (int)(num - n1), num = n1;
      else
        tmp = LEN;
      lseek64(f_ts, n1 - num, SEEK_SET);
      if (read(f_ts, buf, tmp) != tmp) return 1;
    } while ((pos = framesearch_b(buf, 0, tmp, -1)) == -1 && num < n1);
    if (pos != -1) {
      if (write(f_out, buf+pos, tmp-pos) != tmp-pos) return 1;
      n1ret = n1 - (num - pos);
      size_offset -= (num - pos);
      num -= tmp;
      while (num > 0) {
        if (read(f_ts, buf, LEN) != LEN) return 1;
        if (write(f_out, buf, LEN) != LEN) return 1;
        num -= LEN;
      }
    } else {
      n1ret = n1;
    }
    return 0;
  }
  else {
    lseek64(f_ts, n1, SEEK_SET);
    n1ret = n1;
    return 0;
  }
}

int transfer_rest(int f_ts, int f_out, off64_t n1, off64_t n2, off64_t& n2ret)
{
  off64_t i;
  int num, pos, st, pid, tmp;
  char buf[LEN];
  static off64_t lastn2 = -1, lastn2ret;
  if (n1 == lastn2) {
    i = lastn2ret;
    lseek64(f_ts, i, SEEK_SET);
  } else
    i = n1;
  for (; i+LEN<=n2; i+=LEN) {
    if (read(f_ts, buf, LEN) != LEN) return 1;
    if (write(f_out, buf, LEN) != LEN) return 1;
  }
  if (use_leadout) {
    num = read(f_ts, buf, LEN);
    pid = framepid(buf, n2-i);
    st = (i < n2 ? n2-i : 0);
    tmp = -st;
    st += 188;
    while ((pos = framesearch_f(buf, st, num, pid)) == -1 && num == LEN) {
      if (write(f_out, buf, LEN) != LEN) return 1;
      num = read(f_ts, buf, LEN);
      st = 0;
      tmp += LEN;
    }
    if (st && num < st)
      return 1;
    else if (pos == -1) {
      if (write(f_out, buf, num) != num) return 1;
      tmp += num;
      size_offset -= tmp;
    } else {
      if (write(f_out, buf, pos) != pos) return 1;
      tmp += pos;
      size_offset -= tmp;
    }
    lastn2 = n2;
    lastn2ret = n2ret = n2 + tmp;
    return 0;
  } else {
    if (i < n2) {
      if (read(f_ts, buf, n2-i) != n2-i) return 1;
      if (write(f_out, buf, n2-i) != n2-i) return 1;
    }
    lastn2 = lastn2ret = n2ret = n2;
    return 0;
  }
}

int donextinterval1(int fc, int fco, int fa, int fao, int fts, int ftso)
{
  static int n = -1;
  static double tlast, toff = 0.0;
  static off64_t c2;
  off64_t c1, c1ret, c2ret;
  double ttmp;
  unsigned int buf[3];
  unsigned int tmp, lcheck=0;
  if (n==0)
    return 0;
  else if (n==-1) {
    n = lseek(fc, 0, SEEK_END) / 12;
    lseek(fc, 0, SEEK_SET);
    while (1) {
      if (n == 0)
	return 0;
      read(fc, buf, 12);
      n--;
      tmp = byteswop(buf[2]);
      if (tmp == 1) {
        c1 = readoff(fa, fao, 0.0, 1, toff);
        if (transfer_start(fts, ftso, c1, c1ret)) return -1;
        c2 = readoff(fa, fao, inttotime(buf[0], buf[1]), 0, tlast);
        if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
        printf("Interval: %lld - %lld\n", c1ret, c2ret);
	// move all passed marks
	lseek(fc, 0, SEEK_SET);
	read(fc, buf, 12);
	while (byteswop(buf[2]) != 1) {
	  write(fco, buf, 12);
	  read(fc, buf, 12);
	}
	return 1;
      } else if (tmp == 0) {
        c1 = readoff(fa, fao, inttotime(buf[0], buf[1]), 1, toff);
        if (transfer_start(fts, ftso, c1, c1ret)) return -1;
	if (lcheck) {
	  buf[0] = buf[1] = 0;
	  write(fco, buf, 12);
	}
	break;
      } else if (tmp == 3)
	lcheck = 1;
    }
  } else {
    while (1) {
      read(fc, buf, 12);
      n--;
      tmp = byteswop(buf[2]);
      if (tmp == 0) {
        c1 = readoff(fa, fao, inttotime(buf[0], buf[1]), 1, ttmp);
        if (c1 != c2)
          if (transfer_start(fts, ftso, c1, c1ret)) return -1;
        toff += ttmp - tlast;
	break;
      } else if (tmp == 3) {
	timetoint(tlast-toff, buf[0], buf[1]);
	write(fco, buf, 12);
      }
      if (n == 0)
	return 0;
    }
  }
  while (1) {
    if (n == 0) {
      c2 = readoff(fa, fao, -1.0, 0, tlast);
      if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
      printf("Interval: %lld - %lld\n", c1ret, c2ret);
      return 1;
    }
    read(fc, buf, 12);
    n--;
    tmp = byteswop(buf[2]);
    if (tmp == 1) {
      c2 = readoff(fa, fao, inttotime(buf[0], buf[1]), 0, tlast);
      if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
      printf("Interval: %lld - %lld\n", c1ret, c2ret);
      return 1;
    } else if (tmp != 0) {
      timetoint(inttotime(buf[0], buf[1])-toff, buf[0], buf[1]);
      write(fco, buf, 12);
    }
  }
  return 0;
}

int donextinterval2(int barg, int earg, char* argv[], int fc, int fco, int fa, int fao, int fts, int ftso)
{
  static int n = -1, i, lio = -1, lcheck=0;
  static double tlast = 0.0, toff = 0.0;
  static off64_t c2 = -1;
  off64_t c1, c1ret, c2ret;
  double ttmp, ttmp2;
  int j, io = -1;
  unsigned int buf[3];
  unsigned int buff[3];
  unsigned int tmp;
  if (i>=earg) {
    if (!lcheck && n!=-1) {
      lseek(fc, 0, SEEK_SET);
      for (j=0; j<n; j++) {
        read(fc, buf, 12);
        tmp = byteswop(buf[2]);
        if (tmp == 3) {
          timetoint(tlast-toff, buf[0], buf[1]);
          write(fco, buf, 12);
          break;
        }
      }
    }
    if (lio != -1) {  // Add an extra "out" at the end to avoid bug in playback
      buff[2] = byteswop(1);
      timetoint(tlast-toff, buff[0], buff[1]);
      write(fco, buff, 12);
    }
    return 0;
  }
  if (n==-1) {
    i = barg;
    n = lseek(fc, 0, SEEK_END) / 12;
  }
  c1 = readoff(fa, fao, strtotime(argv[i]), 1, ttmp);
  if (c1 != c2)
    if (transfer_start(fts, ftso, c1, c1ret)) return -1;
  toff += ttmp - tlast;
  c2 = readoff(fa, fao, strtotime(argv[i+1]), 0, tlast);
  if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
  printf("Interval: %lld - %lld\n", c1ret, c2ret);
  lseek(fc, 0, SEEK_SET);
  for (j=0; j<n; j++) {
    read(fc, buf, 12);
    tmp = byteswop(buf[2]);
    ttmp2=inttotime(buf[0], buf[1]);
    if (tmp == 3) {
      if (!lcheck) {
        if (ttmp2 <= ttmp) {
          timetoint(ttmp-toff, buf[0], buf[1]);
          write(fco, buf, 12);
          lcheck = 1;
        } else if (ttmp2 <= tlast) {
          timetoint(ttmp2-toff, buf[0], buf[1]);
          write(fco, buf, 12);
          lcheck = 1;
        }
      }
    } else if (ttmp2 >= ttmp && ttmp2 <= tlast) {
      if (tmp < 2) {
        if (lio != io && lio != -1) {
          buff[2] = byteswop(io);
          timetoint(ttmp-toff, buff[0], buff[1]);
          write(fco, buff, 12);
        }
        lio = io = tmp;
      }
      timetoint(ttmp2-toff, buf[0], buf[1]);
      write(fco, buf, 12);
    } else if (tmp < 2) {
      io = tmp;
    }
  }
  i+=2;
  return 1;
}

char* makefilename(const char* base, const char* pre, const char* ext, const char* post)
{
  static char buf[256];
  int len1, len2, len3;
  len1 = strlen(base);
  len2 = (pre ? strlen(pre) : 0);
  len3 = (ext ? strlen(ext) : 0);
  strcpy(buf, base);
  if (ext && len1>=len3 && !strcmp(base+len1-len3,ext))
    len1 -= len3;
  if (pre)
    strcpy(buf+len1, pre);
  if (ext)
    strcpy(buf+len1+len2, ext);
  if (post)
    strcpy(buf+len1+len2+len3, post);
  return buf;
}

void copymeta(int n, int f1, int f2, const char* title, const char* suff, const char* descr)
{ 
  int i, j, k;
  char* buf = new char[n];
  read(f1, buf, n);
  for (i=0; i<n; i++)
    if (buf[i] == 10)
      break;
  write(f2, buf, i);
  if (i == n) return;
  for (j=i+1; j<n; j++)
    if (buf[j] == 10)
      break;
  if (title) {
    write(f2, buf+i, 1);
    for (k=0; title[k] && title[k] != 10; k++);
    write(f2, title, k);
  } else {
    write(f2, buf+i, j-i);
    if (suff && j-i>1)
      write(f2, suff, strlen(suff));
  }
  if (j == n) return;
  i = j;
  for (j=i+1; j<n; j++)
    if (buf[j] == 10)
      break;
  if (descr) {
    write(f2, buf+i, 1);
    for (k=0; descr[k] && descr[k] != 10; k++);
    write(f2, descr, k);
  } else {
    write(f2, buf+i, j-i);
  }
  if (j < n)
    write(f2, buf+j, n-j);
  delete [] buf;
}

int main(int argc, char* argv[])
{
  int f_ts, f_out, f_cuts, f_cutsout, f_ap, f_apout, f_meta, f_metaout;
  char* tmpname;
  const char* suff = 0;
  char* inname = 0;
  char* outname = 0;
  char* title = 0;
  char* descr = 0;
  int cutarg = 0, cutargend = 0;
  int replace = 0;
  int i, j, ok, bad = 0;
  double t1, t2;
  struct stat statbuf;
  struct stat64 statbuf64;

  for (i=1; i<argc; i++) {
    if (!strcmp(argv[i], "-r"))
      replace = 1;
    else if (!strcmp(argv[i], "-o")) {
      if (i == argc-1) {
        bad = 1;
        break;
      }
      outname = argv[++i];
    } else if (!strcmp(argv[i], "-n")) {
      if (i == argc-1) {
        bad = 1;
        break;
      }
      title = argv[++i];
    } else if (!strcmp(argv[i], "-d")) {
      if (i == argc-1) {
        bad = 1;
        break;
      }
      descr = argv[++i];
    } else if (!strcmp(argv[i], "-c")) {
      cutarg = ++i;
      for (j=i; j<argc; j+=2) {
        t1 = strtotime(argv[j]);
        t2 = (j+1<argc ? strtotime(argv[j+1]) : -1.0);
        if (t1 < 0 || t2 < 0)
          break;
        else if (t1 > t2) {
          printf("Bad time interval: %s - %s\n", argv[j], argv[j+1]);
          bad = 1;
          break;
        }
      }
      cutargend = i = j;
      if (bad)
        break;
    } else if (*argv[i] == '-' && (*(argv[i]+1) == 0 ||*(argv[i]+2) == 0)) {
      bad = 1;
      break;
    } else if (!inname)
      inname = argv[i];
    else {
      bad = 1;
      break;
    }
  }
  if (argc == 1 || bad) {
    printf("Usage: mcut [-r] [-o output_ts_file] [-n title] [-d description] ts_file [-c start1 end1 [start2 end2] ... ]\n");
    printf("   -r : Replace (= remove) the original movie.\n");
    printf("   -o : Filename of resulting movie (defaults to the original name appended by \" cut\", unless -r is given).\n");
    printf("   -n : Title of resulting movie.\n");
    printf("   -d : Description of resulting movie.\n");
    printf("   -c : A sequence of starttime and endtime pairs. Each time is given as hour:min:sec. The portion between start and end is retained (i.e. not cut away).\n");
    exit(1);
  }
  if (outname) {
    suff = 0;
  } else {
    outname = inname;
    suff = (replace ? "_" : " cut");
  }
  tmpname = makefilename(inname, 0, ".ts", 0);
  f_ts = open(tmpname, O_RDONLY | O_LARGEFILE);
  if (f_ts == -1) {
    printf("Failed to open input stream file \"%s\"\n", tmpname);
    exit(2);
  }
  tmpname = makefilename(inname, 0, ".ts", ".cuts");
  f_cuts = open(tmpname, O_RDONLY);
  if (f_cuts == -1) {
    printf("Failed to open input cuts file \"%s\"\n", tmpname);
    close(f_ts);
    exit(3);
  }
  tmpname = makefilename(inname, 0, ".ts", ".ap");
  f_ap = open(tmpname, O_RDONLY);
  if (f_ap == -1) {
    printf("Failed to open input ap file \"%s\"\n", tmpname);
    close(f_ts);
    close(f_cuts);
    exit(4);
  }
  if (fstat64(f_ts, &statbuf64)) {
    printf("Failed to stat input stream file.\n");
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    exit(2);
  }
  tmpname = makefilename(outname, suff, ".ts", 0);
  f_out = open(tmpname, O_WRONLY | O_CREAT | O_EXCL | O_LARGEFILE, statbuf64.st_mode & 0xfff);
  if (f_out == -1) {
    printf("Failed to open output stream file \"%s\"\n", tmpname);
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    exit(5);
  }
  if (fstat(f_cuts, &statbuf)) {
    printf("Failed to stat input cuts file.\n");
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    close(f_out);
    unlink(makefilename(outname, suff, ".ts", 0));
    exit(3);
  }
  tmpname = makefilename(outname, suff, ".ts", ".cuts");
  f_cutsout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
  if (f_cutsout == -1) {
    printf("Failed to open output cuts file \"%s\"\n", tmpname);
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    close(f_out);
    unlink(makefilename(outname, suff, ".ts", 0));
    exit(6);
  }
  if (fstat(f_ap, &statbuf)) {
    printf("Failed to stat input ap file.\n");
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    close(f_out);
    close(f_cutsout);
    unlink(makefilename(outname, suff, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", ".cuts"));
    exit(4);
  }
  tmpname = makefilename(outname, suff, ".ts", ".ap");
  f_apout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
  if (f_apout == -1) {
    printf("Failed to open output ap file \"%s\"\n", tmpname);
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    close(f_out);
    close(f_cutsout);
    unlink(makefilename(outname, suff, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", ".cuts"));
    exit(7);
  }

  if (cutarg)
    ok = donextinterval2(cutarg, cutargend, argv, f_cuts, f_cutsout, f_ap, f_apout, f_ts, f_out);
  else
    ok = donextinterval1(f_cuts, f_cutsout, f_ap, f_apout, f_ts, f_out);
  if (!ok) {
    printf("There are no cuts specified. Leaving the movie as it is.\n");
    close(f_ts);
    close(f_cuts);
    close(f_ap);
    close(f_out);
    close(f_cutsout);
    close(f_apout);
    unlink(makefilename(outname, suff, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", ".cuts"));
    unlink(makefilename(outname, suff, ".ts", ".ap"));
    exit(9);
  }

  while (ok > 0) {
    if (cutarg)
      ok = donextinterval2(cutarg, cutargend, argv, f_cuts, f_cutsout, f_ap, f_apout, f_ts, f_out);
    else
      ok = donextinterval1(f_cuts, f_cutsout, f_ap, f_apout, f_ts, f_out);
  }

  close(f_ts);
  close(f_cuts);
  close(f_ap);
  close(f_out);
  close(f_cutsout);
  close(f_apout);
  if (ok < 0) {
    printf("Copying %s failed, read/write error.\n", makefilename(inname, 0, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", ".cuts"));
    unlink(makefilename(outname, suff, ".ts", ".ap"));
    exit(10);
  }

  tmpname = makefilename(inname, 0, ".ts", ".meta");
  f_meta = open(tmpname, O_RDONLY);
  if (f_meta == -1) {
    printf("Failed to open input meta file \"%s\"\n", tmpname);
    exit(0);
  }
  if (fstat(f_meta, &statbuf)) {
    printf("Failed to stat input meta file.\n");
    close(f_meta);
    exit(0);
  }
  tmpname = makefilename(outname, suff, ".ts", ".meta");
  f_metaout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
  if (f_metaout == -1) {
    printf("Failed to open output meta file \"%s\"\n", tmpname);
    close(f_meta);
    exit(0);
  }
  copymeta((int)statbuf.st_size, f_meta, f_metaout, title, (replace ? 0 : suff), descr);
  close(f_meta);
  close(f_metaout);

  if (replace) {
    if (suff) {
      tmpname = makefilename(inname, 0, ".ts", 0);
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      unlink(tmpname);
      rename(makefilename(outname, suff, ".ts", 0), tmpname);
      tmpname = makefilename(inname, 0, ".ts", ".cuts");
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      unlink(tmpname);
      rename(makefilename(outname, suff, ".ts", ".cuts"), tmpname);
      tmpname = makefilename(inname, 0, ".ts", ".ap");
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      unlink(tmpname);
      rename(makefilename(outname, suff, ".ts", ".ap"), tmpname);
      tmpname = makefilename(inname, 0, ".ts", ".meta");
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      unlink(tmpname);
      rename(makefilename(outname, suff, ".ts", ".meta"), tmpname);
    } else {
      unlink(makefilename(inname, 0, ".ts", 0));
      unlink(makefilename(inname, 0, ".ts", ".cuts"));
      unlink(makefilename(inname, 0, ".ts", ".ap"));
      unlink(makefilename(inname, 0, ".ts", ".meta"));
    }
  }
}

