macroScript rdg_multiSubTools
	buttonText:"multiSubTools"
	category:"rdg::preset"
	toolTip:"random MultiSubMat colors ..."
(

	-- -
	-- rdg::multiSubTools
	-- generates MultiSubMaterials with randomized colors
	-- -
	-- 06-06-29	 inital release
	-- -
	-- info@preset.de
	-- -

	global rdg_multiSubTools
	local theIniFile = getDir #plugcfg + "/rdg_tools.ini"
	try(destroyDialog rdg_multiSubTools)catch()

	-- functions
	fn generateRandomMulti = (
		try(
		theMeshSnap = snapshotAsMesh $
		theUsedMatIDs = #()
		for i = 1 to (getNumFaces theMeshSnap) do (
			tempID = (getFaceMatID theMeshSnap i)
			if (findItem theUsedMatIDs tempID) == 0 then (append theUsedMatIDs tempID)
		)
		sort theUsedMatIDs
		delete theMeshSnap
		
		theRandMulti = multiSubMaterial()
		theRandMulti.name = "randomColors"
		theRandMulti.materialIDList = theUsedMatIDs
		for theMat in theRandMulti.materialList do (
			theMat.diffuse = random [0,0,0] [255,255,255]
		)
		$.material = theRandMulti
		)catch()
	
	)
	fn shuffleRandomMulti = (
		try (
			for theMat in $.material.materialList do (
				theMat.diffuse = random [0,0,0] [255,255,255]
			)
	
		)catch()
	)

	-- interface
	rollout rdg_multiSubTools "rdg::multiSubTools" (
		group "random Colors" (
			button action_generate_btn "generate material"
			button action_shuffle_btn  "shuffle colors"
		)
		on action_generate_btn pressed do (
			generateRandomMulti()
		)
		on action_shuffle_btn pressed do (
			shuffleRandomMulti()
		)
		on rdg_multiSubTools moved pos do (
			setIniSetting theIniFile "multiSubTools" "Position" (pos as string)
		)
	)

	-- ui position by bobo
	thePos = execute (getIniSetting theIniFile "multiSubTools" "Position")
	if thePos == OK do thePos = [100,100]
	-- start the show
	createDialog rdg_multiSubTools 150 85 thePos.x thePos.y
)