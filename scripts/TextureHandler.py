import modo

scene = modo.scene.current()
shaderGraph = lx.object.ItemGraph(scene.GraphLookup(lx.symbol.sGRAPH_SHADELOC))

def get_clip(imageMap):
	'''Get clipItem of an imageMap'''

	if imageMap.type == 'imageMap':
		return shaderGraph.FwdByIndex(imageMap, 1)


def get_txtLocator(imageMap):
	'''Get txtLocator of an imageMap'''
	
	if imageMap.type == 'imageMap':
		return shaderGraph.FwdByIndex(imageMap, 0)


def get_shaderTree_pos(item):
	'''Get position of item in shader tree and the parent
	:returns: parentItem, number
	:rtype: tuple
	:param item: modo item
	:type item: modo.Item'''
	
	# imageFolders are special. They are not part of the shader tree so we need to
	# get it assosiating imageMap item
	if item.type == 'imageFolder':
		item_id = modo.Item(shaderGraph.RevByIndex(s, 0)).id
	else:
		item_id = item.id
	
	parent = modo.Item(item_id).parent	
	for i in xrange(parent.childCount()):
		item = parent.childAtIndex(i)
		if item_id == item.id:
			return parent, i


def unpack_imageFolder(imageFolder):
	'''Unpacks an image folder into a mask group.
	Placed above the folder and the folder is disabled
	
	:param imageFolder: imageFolder item
	:type imageFolder: modo.c.IMAGEFOLDER_TYPE
	'''

	if imageFolder.type == 'imageFolder':
		parent, position = get_shaderTree_pos(imageFolder)
		mask = scene.addItem(modo.c.MASK_TYPE, name=imageFolder.name)

		# move goup above image folder
		mask.setParent(parent, position + 1)

		for image in imageFolder.children():
			lx.eval('texture.new clip:{%s}' % image.id)
			lx.eval('texture.parent %s 0' % mask.id)

		lx.eval('shader.setVisible %s false' % shaderGraph.RevByIndex(imageFolder, 0).Ident())
		

def set_bakeRegion(imageMap, renderItem):
	'''Set the bake region of renderItem to the UDIM values of an imageMap'''
	
	videoStill = modo.Item(shaderGraph.FwdByIndex(imageMap, 1))
	udim = videoStill.channel('udim').get()
	
	bake_right = int(str(udim)[3])
	bake_bottom = int(str(udim)[:3]) - 100
	bake_left = bake_right - 1
	bake_top = bake_bottom + 1
	
	lx.eval('channel.value %s channel:{%s:bakeU0}' % (bake_left, renderItem.id))
	lx.eval('channel.value %s channel:{%s:bakeU1}' % (bake_right, renderItem.id))
	lx.eval('channel.value %s channel:{%s:bakeV0}' % (bake_bottom, renderItem.id))
	lx.eval('channel.value %s channel:{%s:bakeV1}' % (bake_top, renderItem.id))
	

def udim_list(udims):
	'''Convert a string list of udims e.g: '1002, 1010, 1005-1016' to
	a list with no duplicates
	
	:param udims: udims
	:type udims: str'''
	
	data = []
	for i in l.split(','):
		i = i.strip()
		print i
		if '-' in i:
			min = i.split('-')[0].strip()
			max = i.split('-')[1].strip()
			for x in xrange(int(min), int(max)+1):
				data.append(x)
		else:
			data.append(int(i))

	return sorted(list(set(data)))