theClasses = exporterPlugin.classes
fbxIndex = findItem theClasses FBXEXP
sceneName = maxFilePath + maxFileName
--exportFile (maxFilePath + "\\tmp" ) #noprompt selectedOnly:on using:theClasses[fbxIndex]


--for obj in rootScene.world.children do (
-- stuff
--)

for g in geometry do
(
	select g
    print g
	exportFile (maxFilePath + "\\" + (g.name as string) ) #noprompt selectedOnly:on using:theClasses[fbxIndex]
) 
