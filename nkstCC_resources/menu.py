import nkstCC_init
if nuke.env['studio']: nuke.menu("Nuke").addMenu("nkstCC").addCommand("Clean Comps",nkstCC_init.main)
else: nuke.menu("Nuke").addMenu("nkstCC").addCommand("Clean Comp",nkstCC_init.main)