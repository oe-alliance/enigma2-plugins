import zipfile

#from Plugins.Extensions.SubsDownloader2.SourceCode import rarfile

#  Copyright (C) 2011 Dawid Bankowski <enigma2subsdownloader@gmail.com>
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.


class zip_extractor():
     def __init__(self, zip__path, destination_dir=None, extracted_extension_filter=None):
          self.__zip__path = zip__path
          self.__destination_dir = destination_dir
          self.__extracted_extension_filter = extracted_extension_filter

     def open_zip_file_to_read(self, zip__path):
          try:
               zip_data = zipfile.ZipFile(zip__path, 'r')
               zip_file_list = zip_data.namelist()
               return zip_data, zip_file_list
               zip_data.close()
          except:
               print "There is problem with %s reading" % zip__path
               return False

     def zipped_file_list(self, zip_file_temp_list, extraction_filter=None):
          zip_file_list = []
          for x in zip_file_temp_list:
               if extraction_filter != None:
                    if x.rsplit(".", 1)[1] in extraction_filter:
                         zip_file_list.append(x)
               else:
                    zip_file_list.append(x)
          return zip_file_list

     def extract_zipped_file(self):
          if self.__destination_dir == None:
               destination_dir = (self.__zip__path.rsplit("/", 1))[0]
          else:
               destination_dir = self.__destination_dir
          if zipfile.is_zipfile(self.__zip__path):
               zip_data, zip_file_list = self.open_zip_file_to_read(self.__zip__path)
               extraction_file_list = self.zipped_file_list(zip_file_list, self.__extracted_extension_filter)
               try:
                    extracted_files_path = []
                    for x in extraction_file_list:
                         zip_data.extract(x, destination_dir)
                         print "Files %s from zip %s extracted to dir: %s.\n" % (x, self.__zip__path, destination_dir)
                         extracted_files_path.append(destination_dir + "/" + x)
                    return extracted_files_path
               except:
                    print "Zip %s was not extracted to dir: %s" % (self.__zip__path, destination_dir)
                    return False
          else:
               print "%s is not a zip file." % zip__path
               return False


"""
class rar_extractor():
     def __init__(self, rar__path, destination_dir = None, extracted_extension_filter = None):
          self.__rar__path = rar__path
          self.__destination_dir = destination_dir
          self.__extracted_extension_filter = extracted_extension_filter

     def open_rar_file_to_read(self,rar__path):
          try:
               rar_data = rarfile.RarFile(rar__path)
               rar_file_list = rar_data.namelist()
               return rar_data,  rar_file_list
               rar_data.close()
          except:
               print "There is problem with %s reading" % rar__path
               return False


     def rared_file_list(self, rar_file_temp_list, extraction_filter = None):
          rar_file_list =[]
          for x in rar_file_temp_list:
               if extraction_filter != None:
                    if x.rsplit(".",1)[1] in extraction_filter:
                         rar_file_list.append(x)
               else:
                    rar_file_list.append(x)
          return rar_file_list


     def extract_rared_file(self):
          if self.__destination_dir == None:
               destination_dir = (self.__rar__path.rsplit("/",1))[0]
          else:
               destination_dir = self.__destination_dir
          if rarfile.is_rarfile(self.__rar__path):
               rar_data, rar_file_list = self.open_rar_file_to_read(self.__rar__path)
               extraction_file_list = self.rared_file_list(rar_file_list, self.__extracted_extension_filter)
               #try:
               extracted_files_path =[]
               for x in extraction_file_list:
                    rar_data.extract(x, destination_dir)
                    print "Files %s from rar %s extracted to dir: %s.\n" % (x,self.__rar__path,destination_dir)
                    extracted_files_path.append(destination_dir+"/"+x)
                    return extracted_files_path
               #except:
               #    print "Rar %s was not extracted to dir: %s" % (self.__rar__path,destination_dir)
               #    return False
          else:
               print "%s is not a rar file." % rar__path
               return False"""

#USE
#zip__path = "C:/1111/Lord of the ring.zip"
#aa = zip_extractor(zip__path,None,("txt","sub","srt"))
#aa.extract_zipped_file()
