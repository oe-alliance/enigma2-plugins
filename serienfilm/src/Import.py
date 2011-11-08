def my_import(name):
#	print "[SF-Plugin]: my_import(%s)" % (name)
	if name == "Components.Converter.ServiceTime":
		name = "Plugins.Extensions.SerienFilm.ServiceTime"
	elif name == "Components.Converter.MovieInfo":
		name = "Plugins.Extensions.SerienFilm.MovieInfo"
	mod = __import__(name)
	components = name.split('.')
	for comp in components[1:]:
		mod = getattr(mod, comp)
	return mod
