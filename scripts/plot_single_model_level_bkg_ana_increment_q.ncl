load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "/home/hailingz/util/panel_two_sets.ncl"



layer     = 87; model level to plot-index starts from 0
;; 62=298hpa; 99=847hpa;75=505hpa,87=699hPa
variable  = "spfh"; variable to plot
plotint   = 2; plot every 3 grids;
outfig    = "pdf" ; plot format
;outfig    = "x11" ; plot format

;;;; EDIT YOUR analysis time for increment plot;;;
anatime    = "2021080418"
assim_freq = 6
hh         = systemfunc("echo "+anatime+" |cut -c9-10")

;;;;;;;;;; EDIT directories
;expt="5obs"
damethod="da"
;DATADir = "/work2/noaa/da/haydenlj/scratch/jedi/fv3/3dhyb/"+expt+"/"
;DATADir = dat+expt+"/"
path=str_split(DATADir,"/")
size=dimsizes(path)
expt=path(size-1)
; forecast initilization time
init_time = systemfunc("/home/hailingz/lib/da_advance_time.exe " + anatime + " -" +assim_freq)
hh_init   = systemfunc("echo "+init_time+" |cut -c9-10")
; files
bkgfile   = addfile(DATADir+init_time+"/atmos/gdas.t"+hh_init+"z.atmf006.nc", "r")
anafile   = addfile(DATADir+anatime+"/atmos/gdas.t"+hh+"z.atmf000.nc", "r")

;;;; variable index in files  ;;;;;;;;
vnamebkg    = getfilevarnames(bkgfile)
vnameana    = getfilevarnames(anafile)
varindxbkg  = ind(vnamebkg.eq.variable)
varindxana  = ind(vnameana.eq.variable)

bkg      = bkgfile->$vnamebkg(varindxbkg)$(0,layer,:,:)
ana      = anafile->$vnameana(varindxana)$(0,layer,:,:)
bkg= bkg*1000.
ana = ana*1000.
inc      = ana - bkg

;;;; coordinate ;;;;;;;
pfull   = bkgfile->pfull
lat     = doubletofloat(bkgfile->grid_yt)
lon     = doubletofloat(bkgfile->grid_xt)
inc!0   = "lat"
inc!1   = "lon"
inc&lat = lat
inc&lon = lon
inc&lat@units = "degrees_north"
inc&lon@units = "degrees_east"
;print(pfull)
wks     = gsn_open_wks(outfig, "inc_"+variable+"_modellevel_"+(layer+1)+"_"+expt+"_"+anatime) 
gsn_define_colormap(wks,"BkBlAqGrYeOrReViWh200"); 

res =True
res@vpXF          = 0.15;
res@vpYF          = 0.85;
res@vpWidthF      = 0.5 ;
res@gsnDraw       = False
res@gsnFrame      = False
;;;; map config
res@gsnAddCyclic      = True
res@mpCenterLonF      = 180
res@tmXBTickSpacingF  = 60;
res@tmYLTickSpacingF  = 30;
res@mpGridAndLimbOn   =  True
res@mpGridLineColor   = "gray55"
res@mpGridLatSpacingF = res@tmYLTickSpacingF
res@mpGridLonSpacingF = res@tmXBTickSpacingF
res@cnFillOn       = True     ; turn on contour fill
res@cnLinesOn      = False    ; turn off contour lines
res@cnLineLabelsOn = False    ; turn off contour line labels
res@pmLabelBarHeightF         = 0.06
res@pmLabelBarWidthF          = 0.45
res@cnLevelSelectionMode      =  "ExplicitLevels"
res@gsnLeftStringFontHeightF  = 0.016
res@lbLabelBarOn        = False

plot = new(2,graphic)
res@gsnRightString = "   "
res@gsnLeftString = "background"; EXPname(is) +" - "+ EXPname(0)
plot(0) = gsn_csm_contour_map(wks,bkg(::plotint,::plotint),res)
res@gsnLeftString = "analysis"
plot(1) = gsn_csm_contour_map(wks,ana(::plotint,::plotint),res)
res@gsnLeftString = "increment"
;res@cnLevels     = (/-4,-3,-2,-1,-0.5,-0.2,-0.1,0.1,0.2,0.5,1,2,3,4/)
;res@cnFillColors = (/15,30,40,45,55,70,90,0,105,120,130,140,150,165,170/)
res@cnLevels     = (/-2,-1,-0.5,-0.2,-0.1,0.1,0.2,0.5,1,2/)
res@cnFillColors = (/20,40,55,70,90,0,105,120,135,155,170/)

plot2   = gsn_csm_contour_map(wks,inc(::plotint,::plotint),res)

;---Panel the two sets of plots
pres1 = True        ; Resources specific to first set of paneled plots
pres2 = True        ; Resources specific to second set of paneled plots
pres  = True        ; For setting the area of paneled plots
pres1@pmLabelBarOrthogonalPosF = -0.02    ; Move closer to plots
pres2@pmLabelBarOrthogonalPosF = -0.02
pres@gsnPanelTop    = 0.93
pres@gsnPanelLeft   = 0.0
pres@gsnPanelBottom = 0.0
pres@gsnPanelRight  = 1.0

pres1@gsnPanelMainString = "              "+variable +" (g/kg) at " + anatime + " ~C~ model level "+ (layer+1)+" (Ref Pressure="+tointeger(pfull(layer))+"(hPa))"
pres1@txFontHeightF = 0.017 
panel_two_sets(wks,plot,plot2,(/2,1/),(/1,1/),pres1,pres2,pres)
