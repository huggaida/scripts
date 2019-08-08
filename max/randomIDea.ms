utility randomidea "Random IDea"
(
spinner low "Low: " range:[1,64,1] type:#integer align:#left
spinner hig "High:" range:[1,64,16] type:#integer align:#left
button randomizeID "Randomize IDea's" align:#left

global farr = #()
global fbitarr = #{}
global f

on randomizeID pressed do
	(
	f = 1
	if selection.count != 1 then messageBox "Please select ONE editable poly."  beep:false else
		(
		m = selection
		convertTo m (Editable_Poly)
		facecount = m[1].GetNumFaces()
		--print facecount
		facecheck = (f<facecount)
		for i in 1 to facecount while facecheck do
			(
			farr = #()
			fbitarr = #{}
			m[1].editablepoly.setselection #face #{f}
			m[1].selectelement()
			fbitarr = polyop.GetFaceSelection m[1]
			polyop.SetFaceMatID m[1] fbitarr ((random low.value hig.value) as integer)
			--print fbitarr
			farr = fbitarr as array
			--print farr
			f = (farr[farr.count] + 1)
			facecheck = (f<facecount)
			--print f
			)
		)
	)
)