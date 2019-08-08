my_METAL = $Metal
my_GLASS   = $Glass
my_PLASTIC = $Plastic

m = netrender.getmanager()
m.connect #automatic "192.168.1.112"
m.getcontrol() --takes queue control
m.wantControl=true --if another client does QueryControl(), they will get a return value of false

Grange = #(2,5,6,7,8)
Mrange = #(13,14,15,16,17)
for  k in Mrange do 
	for  n in Grange do 
		--print (k as string+"_"+n as string)
--for  k = 13 to 17 do
	--for n = 1 to 8  do	
		
		(
			my_GLASS.material = meditMaterials[n]
			my_METAL.material = meditMaterials[k]

			if k <= 15 then my_PLASTIC.material = meditMaterials[20] else my_PLASTIC.material = meditMaterials[19]


			job = m.newjob()
			job.fromFrame = 0
			job.toFrame = 0
			job.Suspend()
			job.name  = (getFilenameFile maxfilename) +"_" +(meditMaterials[k].name as string) +"_" + (meditMaterials[n].name as string)
			dirName = "\\\\Buch-pc\\render\\Dush_Konfig\\RENDER_KONFIG_STANDART\\" + (getFilenameFile maxfilename)
			makeDir  dirName
			job.frameOutputName =  "\\\\Buch-pc\\render\\Dush_Konfig\\RENDER_KONFIG_STANDART\\" + (getFilenameFile maxfilename) +"\\"+ (getFilenameFile maxfilename) + "_" + (meditMaterials[k].name as string) +"_"+ (meditMaterials[n].name as string) + ".tif"
			job.submit()

      --job.Suspend() 

		)

 m.Disconnect()
