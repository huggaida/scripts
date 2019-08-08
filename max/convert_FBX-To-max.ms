theClasses = importerPlugin.classes
fbxIndex = findItem theClasses FBXIMP


fn getFilesRecursive root pattern =
(
dir_array = GetDirectories (root+"/*")
for d in dir_array do
  join dir_array (GetDirectories (d+"/*"))
my_files = #()
for f in dir_array do
  join my_files (getFiles (f + pattern))
my_files
)

my_files = getFilesRecursive maxFilePath "*.fbx"

for f in my_files do (
	
	--select geometry
	delete geometry
	my_name = getFilenameFile f
	my_path = getFilenamePath f
	my_name = my_path +  my_name +  ".max"
	importFile (f) #noprompt  using:theClasses[fbxIndex]
	macros.run "Modifier Stack" "Convert_to_Poly"
	saveMaxFile my_name
)

