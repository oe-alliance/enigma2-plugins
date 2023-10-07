 /* Copyright (C) 2007, 2008, 2009 Anders Holst
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
#include <byteswap.h>

#define LEN 24064

static off64_t time_offset;
static off64_t size_offset;
static off64_t curr_size_offset;

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

double inttotime(unsigned int t1, unsigned int t2)
{
  return (be32toh(t2)*1.1111111111111112e-05 + be32toh(t1)*47721.858844444447);
}

double lltotime(long long int t)
{
  return ((unsigned int)(t&0xffffffff)*1.1111111111111112e-05) + ((unsigned int)(t>>32)*47721.858844444447);
}

void timetoint(double tm, unsigned int& t1, unsigned int& t2)
{
  double tmp=tm/47721.858844444447;
  t1 = htobe32((unsigned int)tmp);
  t2 = htobe32((unsigned int)((tm - t1*47721.858844444447)*90000));
}

void swapbuf(off64_t buf0[], off64_t buf1[])
{
  off64_t buf[2];
  buf[0] = buf0[0];
  buf[1] = buf0[1];
  buf0[0] = buf1[0];
  buf0[1] = buf1[1];
  buf1[0] = buf[0];
  buf1[1] = buf[1];
}

int readbufinternal(int f, off64_t buf[])
{
  if (read(f, buf, 16) != 16)
    return 0;
  buf[0] = (off64_t)be64toh((unsigned long long int)buf[0]);
  buf[1] = (off64_t)be64toh((unsigned long long int)buf[1]);
  return 1;
}

void writebufinternal(int f, off64_t buf[])
{
  off64_t tbuf[2];
  tbuf[0] = (off64_t)htobe64((unsigned long long int)buf[0] - curr_size_offset);
  tbuf[1] = (off64_t)htobe64((unsigned long long int)buf[1]);
  write(f, tbuf, 16);
}

void movesc(int fs, int fso, off64_t off, int beg)
{
  static off64_t buf[2];
  static off64_t lastoff = 0;
  static int endp = 0;
  if (fs == -1 || fso == -1)
    return;
  if (off < lastoff) {
    lseek(fs, 0, SEEK_SET);
    lastoff = 0;
    endp = 0;
  }
  if (off == lastoff || endp)
    return;
  lastoff = off;
  if (!beg && !endp)
    writebufinternal(fso, buf);
  while (readbufinternal(fs, buf)) {
    if (buf[0] >= off)
      return;
    if (!beg)
      writebufinternal(fso, buf);
  }
  endp = 1;
}

off64_t readoff(int fa, int fao, int fs, int fso, double t, int beg, double& tr)
{
  static off64_t buf0[2];
  static off64_t buf1[2];
  static bool buffilled = false;
  static off64_t lastreturn = 0;
  static double last = 0.0;
  static int endp = 0;
  off64_t sizetmp = 0;
  double tt, lt;
  if (!buffilled) {
    if (!(readbufinternal(fa, buf0) && readbufinternal(fa, buf1))) {
      printf("The corresponding \".ap\"-file is empty.\n");
      exit(8);
    }
    buffilled = true;
    time_offset = buf0[1];
    if (buf1[1] > buf0[1] && buf1[1] - buf0[1] < 900000)
      time_offset -= (buf1[1]-buf0[1])*buf0[0]/(buf1[0]-buf0[0]);
    else if (buf1[1] > buf0[1] || buf0[1] - buf1[1] > 45000)
      time_offset = buf1[1];
    size_offset = buf0[0];
    lastreturn = 0;
    last = 0.0;
    endp = 0;
  }
  if (t < last && t != -1.0) {
    sizetmp = buf0[0];
    lseek(fa, 0, SEEK_SET);
    readbufinternal(fa, buf0);
    readbufinternal(fa, buf1);
    time_offset = buf0[1];
    if (buf1[1] > buf0[1] && buf1[1] - buf0[1] < 900000)
      time_offset -= (buf1[1]-buf0[1])*buf0[0]/(buf1[0]-buf0[0]);
    else if (buf1[1] > buf0[1] || buf0[1] - buf1[1] > 45000)
      time_offset = buf1[1];
    size_offset += buf0[0] - sizetmp;
    lastreturn = 0;
    last = 0.0;
    endp = 0;
  }
  if (t == last || endp == 1) {
    return lastreturn;
  }
  if (!beg)
    writebufinternal(fao, buf0);
  last = t;
  lt = lltotime(buf0[1] - time_offset);
  if (buf0[1] - buf1[1] > 0 && buf0[1] - buf1[1] <= 45000)
    tt = lt, buf1[1] = buf0[1];
  else
    tt = lltotime(buf1[1] - time_offset);
  sizetmp = buf0[0];
  while (tt < t || t == -1.0) {
    swapbuf(buf0, buf1);
    if (!readbufinternal(fa, buf1))
      endp = 1;
    if (!beg)
      writebufinternal(fao, buf0);
    if (endp)
      break;
    if (buf0[1] - buf1[1] > 45000 || buf1[1] - buf0[1] > 900000) {
      if (absless(buf1[1] + (((long long int)1) << 33) - buf0[1], 900000))
        time_offset -= ((long long int)1) << 33;
      else
        time_offset += buf1[1] - buf0[1];
    }
    lt = tt;
    if (buf0[1] - buf1[1] > 0 && buf0[1] - buf1[1] <= 45000)
      tt = lt, buf1[1] = buf0[1];
    else
      tt = lltotime(buf1[1] - time_offset);
  }
  if (endp) {
    tr = tt;
  } else if (beg ? (lt == tt || (t-lt > tt-t && tt-t<0.18)) : (t-lt >= tt-t || t-lt>0.18)) {
    swapbuf(buf0, buf1);
    if (!readbufinternal(fa, buf1))
      endp = 1;
    if (buf0[1] - buf1[1] > 0 && buf0[1] - buf1[1] <= 45000)
      buf1[1] = buf0[1];
    if (!beg)
      writebufinternal(fao, buf0);
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

int framesearch_f(char* buf, int start, int stop, int pid, int& tp)
{
  char* p;
  int pos = -1;
  for (p = buf+start; p < buf+stop-5; p++)
    if (p[0]==0 && p[1]==0 && p[2]==1) {
      if (p[3]==0) {
        pos = ((p - buf)/188)*188;
        if (pid == -1 || framepid(buf, pos) == pid) {
          tp = (p[5]>>3)&7;
          return pos;
        }
      } else if (p[3]==0x09) {
        pos = ((p - buf)/188)*188;
        if ((buf[pos+1] & 0x40) && (pid == -1 || framepid(buf, pos) == pid)) {
          tp = (p[4] >> 5) + 1;
          return pos;
        }
      } else if ((p[3] >> 1)==35) {
        pos = ((p - buf)/188)*188;
        if ((buf[pos+1] & 0x40) && (pid == -1 || framepid(buf, pos) == pid)) {
          tp = (p[5] >> 5) + 1;
          return pos;
        }
      }
    }
  return -1;
}

int framesearch_b(char* buf, int start, int stop, int pid)
{
  char* p;
  int pos = -1;
  for (p = buf+stop-1; p >= buf+start+3; p--)
    if (p[-1]==1 && p[-2]==0 && p[-3]==0) {
      if (p[0]==0) {
        pos = ((p - buf)/188)*188;
        if (pid == -1 || framepid(buf, pos) == pid)
          return pos;
      } else if (p[0]==0x09 || (p[0] >> 1)==35) {
        pos = ((p - buf)/188)*188;
        if ((buf[pos+1] & 0x40) && (pid == -1 || framepid(buf, pos) == pid))
          return pos;
      }
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
  int num, pos, st, pid, tp, tmp;
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
    while ((pos = framesearch_f(buf, st, num, pid, tp)) == -1 ? num == LEN : tp == 3) {
      if (pos != -1) {
        st = pos + 188;
      } else {
        if (write(f_out, buf, LEN) != LEN) return 1;
        num = read(f_ts, buf, LEN);
        st = 0;
        tmp += LEN;
      }
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

int donextinterval1(int fc, int fco, int fa, int fao, int fs, int fso, int fts, int ftso)
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
      tmp = be32toh(buf[2]);
      if (tmp == 1) {
        c1 = readoff(fa, fao, fs, fso, 0.0, 1, toff);
        if (transfer_start(fts, ftso, c1, c1ret)) return -1;
        curr_size_offset = size_offset;
        movesc(fs, fso, c1ret, 1);
        c2 = readoff(fa, fao, fs, fso, inttotime(buf[0], buf[1]), 0, tlast);
        if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
        movesc(fs, fso, c2ret, 0);
        printf("Interval: %lld - %lld\n", c1ret, c2ret);
        // move all passed marks
        lseek(fc, 0, SEEK_SET);
        read(fc, buf, 12);
        while (be32toh(buf[2]) != 1) {
          write(fco, buf, 12);
          read(fc, buf, 12);
        }
        return 1;
      } else if (tmp == 0) {
        c1 = readoff(fa, fao, fs, fso, inttotime(buf[0], buf[1]), 1, toff);
        if (transfer_start(fts, ftso, c1, c1ret)) return -1;
        curr_size_offset = size_offset;
        movesc(fs, fso, c1ret, 1);
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
      tmp = be32toh(buf[2]);
      if (tmp == 0) {
        c1 = readoff(fa, fao, fs, fso, inttotime(buf[0], buf[1]), 1, ttmp);
        use_leadin = 0;
        if (c1 != c2) {
          if (transfer_start(fts, ftso, c1, c1ret)) return -1;
          curr_size_offset = size_offset;
        } else {
          c1ret = c2ret;
          size_offset = curr_size_offset;
        }
        movesc(fs, fso, c1ret, 1);
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
      c2 = readoff(fa, fao, fs, fso, -1.0, 0, tlast);
      if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
      movesc(fs, fso, c2ret, 0);
      printf("Interval: %lld - %lld\n", c1ret, c2ret);
      return 1;
    }
    read(fc, buf, 12);
    n--;
    tmp = be32toh(buf[2]);
    if (tmp == 1) {
      c2 = readoff(fa, fao, fs, fso, inttotime(buf[0], buf[1]), 0, tlast);
      if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
      movesc(fs, fso, c2ret, 0);
      printf("Interval: %lld - %lld\n", c1ret, c2ret);
      return 1;
    } else if (tmp != 0) {
      timetoint(inttotime(buf[0], buf[1])-toff, buf[0], buf[1]);
      write(fco, buf, 12);
    }
  }
  return 0;
}

int donextinterval2(int barg, int earg, char* argv[], int fc, int fco, int fa, int fao, int fs, int fso, int fts, int ftso)
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
    if (!lcheck && n>0) {
      lseek(fc, 0, SEEK_SET);
      for (j=0; j<n; j++) {
        read(fc, buf, 12);
        tmp = be32toh(buf[2]);
        if (tmp == 3) {
          timetoint(tlast-toff, buf[0], buf[1]);
          write(fco, buf, 12);
          break;
        }
      }
    }
    return 0;
  }
  if (n==-1) {
    i = barg;
    n = (fc != -1 ? lseek(fc, 0, SEEK_END) / 12 : 0);
  }
  c1 = readoff(fa, fao, fs, fso, strtotime(argv[i]), 1, ttmp);
  if (c1 != c2) {
    if (transfer_start(fts, ftso, c1, c1ret)) return -1;
    curr_size_offset = size_offset;
  } else {
    c1ret = c2ret;
    size_offset = curr_size_offset;
  }
  movesc(fs, fso, c1ret, 1);
  use_leadin = 0;
  toff += ttmp - tlast;
  c2 = readoff(fa, fao, fs, fso, strtotime(argv[i+1]), 0, tlast);
  if (transfer_rest(fts, ftso, c1, c2, c2ret)) return -1;
  movesc(fs, fso, c2ret, 0);
  printf("Interval: %lld - %lld\n", c1ret, c2ret);
  if (n > 0) lseek(fc, 0, SEEK_SET);
  for (j=0; j<n; j++) {
    read(fc, buf, 12);
    tmp = be32toh(buf[2]);
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
          buff[2] = htobe32(io);
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

char* makefilename(const char* base, const char* pre, const char* ext, const char* post, int delext = 0)
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
  if (ext && !delext)
    strcpy(buf+len1+len2, ext);
  if (post)
    strcpy(buf+len1+len2+(delext ? 0 : len3), post);
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
  if (i == n) goto exit;
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
  if (j == n) goto exit;
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
  /* creation time */
  i = j;
  for (j=i+1; j<n; j++)
    if (buf[j] == 10)
      break;
  write(f2, buf+i, j-i);
  /* tags */
  i = j;
  for (j=i+1; j<n; j++)
    if (buf[j] == 10)
      break;
  write(f2, buf+i, j-i);
  /* length in pts */
  i = j;
  for (j=i+1; j<n; j++)
    if (buf[j] == 10)
      break;
  write(f2, buf+i, 1);
  /* write 0, force length to be re-calculated */
  write(f2, "0", 1);
  /* file size */
  i = j;
  for (j=i+1; j<n; j++)
    if (buf[j] == 10)
      break;
  write(f2, buf+i, 1);
  /* write 0, force size to be re-calculated */
  write(f2, "0", 1);
  /* remaining fields */
  if (j < n)
    write(f2, buf+j, n-j);
exit:
  delete [] buf;
}

void copysmallfile(int n, int f1, int f2)
{ 
  char* buf = new char[n];
  read(f1, buf, n);
  write(f2, buf, n);
  delete [] buf;
}

int main(int argc, char* argv[])
{
  int f_ts, f_out, f_cuts, f_cutsout, f_ap, f_apout, f_sc, f_scout = -1, f_meta, f_metaout, f_eit, f_eitout;
  char* tmpname;
  const char* suff = 0;
  char* inname = 0;
  char* outname = 0;
  char* title = 0;
  char* descr = 0;
  int cutarg = 0, cutargend = 0;
  int replace = 0, metafailed = 0;
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
    suff = (replace ? ".tmpcut" : " cut");
  }
  tmpname = makefilename(inname, 0, ".ts", 0);
  f_ts = open(tmpname, O_RDONLY | O_LARGEFILE);
  if (f_ts == -1) {
    printf("Failed to open input stream file \"%s\"\n", tmpname);
    exit(2);
  }
  tmpname = makefilename(inname, 0, ".ts", ".cuts");
  f_cuts = open(tmpname, O_RDONLY);
  if (f_cuts == -1 && !cutarg) {
    printf("Failed to open input cuts file \"%s\"\n", tmpname);
    close(f_ts);
    exit(3);
  }
  tmpname = makefilename(inname, 0, ".ts", ".ap");
  f_ap = open(tmpname, O_RDONLY);
  if (f_ap == -1) {
    printf("Failed to open input ap file \"%s\"\n", tmpname);
    close(f_ts);
    if (f_cuts != -1) close(f_cuts);
    exit(4);
  }
  tmpname = makefilename(inname, 0, ".ts", ".sc");
  f_sc = open(tmpname, O_RDONLY);

  if (fstat64(f_ts, &statbuf64)) {
    printf("Failed to stat input stream file.\n");
    close(f_ts);
    close(f_ap);
    if (f_sc != -1) close(f_sc);
    if (f_cuts != -1) close(f_cuts);
    exit(2);
  }
  tmpname = makefilename(outname, suff, ".ts", 0);
  f_out = open(tmpname, O_WRONLY | O_CREAT | O_EXCL | O_LARGEFILE, statbuf64.st_mode & 0xfff);
  if (f_out == -1) {
    printf("Failed to open output stream file \"%s\"\n", tmpname);
    close(f_ts);
    close(f_ap);
    if (f_sc != -1) close(f_sc);
    if (f_cuts != -1) close(f_cuts);
    exit(5);
  }
  if (f_cuts != -1 && fstat(f_cuts, &statbuf)) {
    if (!cutarg) {
      printf("Failed to stat input cuts file.\n");
      close(f_ts);
      close(f_out);
      close(f_ap);
      if (f_sc != -1) close(f_sc);
      close(f_cuts);
      unlink(makefilename(outname, suff, ".ts", 0));
      exit(3);
    } else {
      close(f_cuts);
      f_cuts = -1;
    }
  }
  if (f_cuts != -1) {
    tmpname = makefilename(outname, suff, ".ts", ".cuts");
    f_cutsout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
    if (f_cutsout == -1) {
      printf("Failed to open output cuts file \"%s\"\n", tmpname);
      close(f_ts);
      close(f_out);
      close(f_ap);
      if (f_sc != -1) close(f_sc);
      close(f_cuts);
      unlink(makefilename(outname, suff, ".ts", 0));
      exit(6);
    }
  } else
    f_cutsout = -1;
  if (fstat(f_ap, &statbuf)) {
    printf("Failed to stat input ap file.\n");
    close(f_ts);
    close(f_out);
    close(f_ap);
    if (f_sc != -1) close(f_sc);
    if (f_cuts != -1) {
      close(f_cuts);
      close(f_cutsout);
      unlink(makefilename(outname, suff, ".ts", ".cuts"));
    }
    unlink(makefilename(outname, suff, ".ts", 0));
    exit(4);
  }
  tmpname = makefilename(outname, suff, ".ts", ".ap");
  f_apout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
  if (f_apout == -1) {
    printf("Failed to open output ap file \"%s\"\n", tmpname);
    close(f_ts);
    close(f_out);
    close(f_ap);
    if (f_sc != -1) close(f_sc);
    if (f_cuts != -1) {
      close(f_cuts);
      close(f_cutsout);
      unlink(makefilename(outname, suff, ".ts", ".cuts"));
    }
    unlink(makefilename(outname, suff, ".ts", 0));
    exit(7);
  }
  if (f_sc != -1 && fstat(f_sc, &statbuf)) {
    close(f_sc);
    f_sc = -1;
  }
  if (f_sc != -1) {
    tmpname = makefilename(outname, suff, ".ts", ".sc");
    f_scout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
    if (f_scout == -1) {
      printf("Failed to open output sc file \"%s\"\n", tmpname);
      close(f_ts);
      close(f_out);
      close(f_ap);
      close(f_apout);
      close(f_sc);
      if (f_cuts != -1) {
        close(f_cuts);
        close(f_cutsout);
        unlink(makefilename(outname, suff, ".ts", ".cuts"));
      }
      unlink(makefilename(outname, suff, ".ts", 0));
      unlink(makefilename(outname, suff, ".ts", ".ap"));
      exit(7);
    }
  }
  if (cutarg)
    ok = donextinterval2(cutarg, cutargend, argv, f_cuts, f_cutsout, f_ap, f_apout, f_sc, f_scout, f_ts, f_out);
  else
    ok = donextinterval1(f_cuts, f_cutsout, f_ap, f_apout, f_sc, f_scout, f_ts, f_out);
  if (!ok) {
    printf("There are no cuts specified. Leaving the movie as it is.\n");
    close(f_ts);
    close(f_out);
    close(f_ap);
    close(f_apout);
    if (f_cuts != -1) {
      close(f_cuts);
      close(f_cutsout);
      unlink(makefilename(outname, suff, ".ts", ".cuts"));
    }
    if (f_sc != -1) {
      close(f_sc);
      close(f_scout);
      unlink(makefilename(outname, suff, ".ts", ".sc"));
    }
    unlink(makefilename(outname, suff, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", ".ap"));
    exit(9);
  }

  while (ok > 0) {
    if (cutarg)
      ok = donextinterval2(cutarg, cutargend, argv, f_cuts, f_cutsout, f_ap, f_apout, f_sc, f_scout, f_ts, f_out);
    else
      ok = donextinterval1(f_cuts, f_cutsout, f_ap, f_apout, f_sc, f_scout, f_ts, f_out);
  }

  close(f_ts);
  close(f_out);
  close(f_ap);
  close(f_apout);
  if (f_cuts != -1) {
    close(f_cuts);
    close(f_cutsout);
  }
  if (f_sc != -1) {
    close(f_sc);
    close(f_scout);
  }
  if (ok < 0) {
    printf("Copying %s failed, read/write error.\n", makefilename(inname, 0, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", 0));
    unlink(makefilename(outname, suff, ".ts", ".ap"));
    if (f_cuts != -1)
      unlink(makefilename(outname, suff, ".ts", ".cuts"));
    if (f_sc != -1)
      unlink(makefilename(outname, suff, ".ts", ".sc"));
    exit(10);
  }

  if (!replace) {
    tmpname = makefilename(inname, 0, ".ts", ".eit", 1);
    f_eit = open(tmpname, O_RDONLY);
    if (f_eit != -1) {
      if (fstat(f_eit, &statbuf))
        close(f_eit);
      else {
        tmpname = makefilename(outname, suff, ".ts", ".eit", 1);
        f_eitout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
        if (f_eitout == -1)
          close(f_eit);
        else {
          copysmallfile((int)statbuf.st_size, f_eit, f_eitout);
          close(f_eit);
          close(f_eitout);
        }
      }
    }
  }

  metafailed = 0;
  tmpname = makefilename(inname, 0, ".ts", ".meta");
  f_meta = open(tmpname, O_RDONLY);
  if (f_meta == -1) {
    metafailed = 1;
  } else if (fstat(f_meta, &statbuf)) {
    metafailed = 1;
    close(f_meta);
  } else {
    tmpname = makefilename(outname, suff, ".ts", ".meta");
    f_metaout = open(tmpname, O_WRONLY | O_CREAT | O_TRUNC, statbuf.st_mode & 0xfff);
    if (f_metaout == -1) {
      metafailed = 1;
      close(f_meta);
    } else {
      copymeta((int)statbuf.st_size, f_meta, f_metaout, title, (replace ? 0 : suff), descr);
      close(f_meta);
      close(f_metaout);
    }
  }

  if (replace) {
    if (suff) {
      tmpname = makefilename(inname, 0, ".ts", 0);
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      unlink(tmpname);
      rename(makefilename(outname, suff, ".ts", 0), tmpname);
      tmpname = makefilename(inname, 0, ".ts", ".ap");
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      unlink(tmpname);
      rename(makefilename(outname, suff, ".ts", ".ap"), tmpname);
      if (f_sc != -1) {
        tmpname = makefilename(inname, 0, ".ts", ".sc");
        tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
        unlink(tmpname);
        rename(makefilename(outname, suff, ".ts", ".sc"), tmpname);
      }
      if (f_cuts != -1) {
        tmpname = makefilename(inname, 0, ".ts", ".cuts");
        tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
        unlink(tmpname);
        rename(makefilename(outname, suff, ".ts", ".cuts"), tmpname);
      }
      if (!metafailed) {
        tmpname = makefilename(inname, 0, ".ts", ".meta");
        tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
        unlink(tmpname);
        rename(makefilename(outname, suff, ".ts", ".meta"), tmpname);
      }
    } else {
      unlink(makefilename(inname, 0, ".ts", 0));
      unlink(makefilename(inname, 0, ".ts", ".ap"));
      if (f_sc != -1)
        unlink(makefilename(inname, 0, ".ts", ".sc"));
      if (f_cuts != -1)
        unlink(makefilename(inname, 0, ".ts", ".cuts"));
      tmpname = makefilename(inname, 0, ".ts", ".eit", 1);
      tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
      rename(tmpname, makefilename(outname, 0, ".ts", ".eit", 1));
      if (!metafailed) 
        unlink(makefilename(inname, 0, ".ts", ".meta"));
      else {
        tmpname = makefilename(inname, 0, ".ts", ".meta");
        tmpname = strcpy(new char[strlen(tmpname)+1], tmpname);
        rename(tmpname, makefilename(outname, 0, ".ts", ".meta"));
      }
    }
  }
}

