file="g:\\subdir1\\subdir2\\myImage.jpg"
filenameFromPath file -- returns: "myImage.jpg"
getFilenamePath file -- returns: "g:\subdir1\subdir2\"
getFilenameFile file -- returns: "myImage"
getFilenameType file -- returns: ".jpg"
pathIsNetworkPath "c:\\temp\\test.txt" --returns: false
pathIsNetworkPath "\\\\someserver\\temp\\test.txt" --returns: true