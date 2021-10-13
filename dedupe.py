## This file is used to deduplicate and remove irregularities from the match list
import glob
import os


def DedupeFiles(pathToFile,outputPath):
   ## read all files and complile a larger list
   path = pathToFile
   list_of_lines = []
   for filename in glob.glob(os.path.join(os.getcwd(),path, '*.txt')):
      with open(filename, 'r') as f:
         lines = f.readlines()
         list_of_lines.extend(lines)
   print('Original length: ', len(list_of_lines))

   dedupedList = list(dict.fromkeys(list_of_lines))

   print('Final length: ', len(dedupedList))
   print(dedupedList[0])
   ## Save to file, so we don't have to run this all the time
   textfile = open(f"{outputPath}.txt", "w")
   for item in dedupedList:
      textfile.write(str(item))
   textfile.close()

## Does not require.txt extension in parameter
## COMMENTED OUT BECAUSE IT ONLY NEEDS TO RUN ONCE!
# DedupeFiles("matchlist","matchList/matchIDListDedupe")


## Requires .txt extention in parameter
# params: path to the file, list of keys
## Removed IDs that do not fit the regular format starting with: EUW1_
def RemoveIrregularities(pathToFile,keys,outputPath):
   matchList = []
   with open(pathToFile, 'r') as f:
      lines = f.read().splitlines()
      print(f"Length before filter: {len(lines)}")
      newList = list(filter(lambda item: item[:5] == keys[0] or item[:5] == keys[1], lines))
      print(f"Length after filter: {len(newList)}")

      textfile = open(f"{outputPath}.txt", "w")
      for item in newList:
         textfile.write(str(item) + "\n")
      textfile.close()


