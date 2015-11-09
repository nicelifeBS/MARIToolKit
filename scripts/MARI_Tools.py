#python

"""
MARI TOOLs
Bjoern Siegert aka nicelife

Arguments:
loadFiles, gammaCorrect, setUVoffset, sortSelection, createPolySets

Import textures from MARI and some tools to manage these:
For import the user can choose:
- a delimiter so that the script can find the UDIM number
- to ignore the 8x8 pixel textures from import
- if the textures should be gamma corrected
- Create ENTITY and UDIM masks in shader tree

Tools:
- Sets the UV offset automatically from the file name
- Gamma correction of imported texutres if needed
- Sort the images in scene tree in alphabetic order
- Create polygon sets for each UDIM
"""

import re
import lx
import lxu.select

def locator_ID(imageMap_ID):
    """
    Find ID of the texture locator of an image map. The ID of the image map in the shadertree is needed as argument.
    """
    layerservice.select('texture.N', 'all')
    texture_num = layerservice.query('texture.N')
    # Parse through all textures until texture ID of layer matches the selected one.
    for i in xrange(texture_num):
        layerservice.select('texture.id', str(i))
        texture_ID = layerservice.query('texture.id')
        if texture_ID == imageMap_ID:            
            return layerservice.query('texture.locator') #retruns the texture locator ID

def create_imageMap(clipName, uvmap, UVoffSet):
    """
    Create texture in shader tree with the given file and UVoffset values.
    Returns imageMap.id
    """
    lx.eval("shader.create constant")
    lx.eval("item.setType imageMap textureLayer")
    lx.eval("texture.setIMap {%s}" %clipName)
    lx.eval("item.channel txtrLocator$useUDIM false")
    lx.eval("item.channel imageMap$aa false")
    lx.eval("item.channel txtrLocator$projType uv")
    lx.eval("texture.setUV {%s}" %uvmap)
    lx.eval("item.channel txtrLocator$tileU reset")
    lx.eval("item.channel txtrLocator$tileV reset")
    lx.eval("item.channel txtrLocator$m02 %s" %UVoffSet[0])
    lx.eval("item.channel txtrLocator$m12 %s" %UVoffSet[1])
    
    sceneservice.select('selection', 'imageMap')
    imageMapID = sceneservice.query('selection')
    return imageMapID

def create_imageMapFromFolder(imageFolderID, uvmap):
    """Create image map with an imageFolder. This will use the automatic UDIM from modo"""
    lx.eval("shader.create constant")
    lx.eval("item.setType imageMap textureLayer")
    lx.eval("texture.setIMap {%s}" %imageFolderID)
    lx.eval("item.channel txtrLocator$useUDIM true")
    lx.eval("item.channel imageMap$aa false")
    lx.eval("item.channel txtrLocator$projType uv")
    lx.eval("texture.setUV {%s}" %uvmap)    
    
    sceneservice.select('selection', 'imageMap')
    imageMapID = sceneservice.query('selection')
    return imageMapID
    
    
def load_files():
    """
    Load in files and save complete paths in a list
    """
    try:
        lx.eval("dialog.setup fileOpenMulti")
        lx.eval("dialog.title {Import MARI textures}")
        lx.eval("dialog.result ok")
        lx.eval("dialog.open")
        
        return lx.evalN("dialog.result ?")
    
    except RuntimeError:
        return False


def get_file_extension(filename):
    """returns the file extension, e.g. ".tif". Searches from end until it finds "." """
    file_extension = ""
    
    for i in filename[::-1]: # reverse the filename and walkthrough all chars and add each one to variable until finding the first period
        if i !=".":
            file_extension += i
        else:
            break
        
    return "." + file_extension[::-1] # return the saved extension by reversing it back and adding the period


def get_filename(filePath):
    """returns the file name without the extension -> clip name"""
    filename = filePath.split("/")[-1]
    return filename.replace(get_file_extension(filename), "")


def create_TagsFromFilename(fileNameUser, fileName):    
    """Extract MARI variables from filename (without extension).
    Returns a dictionary with all found variables and their values:
    {'$CHA':'diffuse','$UDI':'1002','$ENT':'Mesh'}"""
    
    # MARI filename variables
    MARI_vars = ["$ENTITY", "$CHANNEL", "$UDIM", "$LAYER", "$FRAME", "$NUMBER", "$COUNT", "$[METADATA VALUE]"]
    
    foundMARI_vars = []
    for i in MARI_vars:
        if i in fileNameUser:
            foundMARI_vars.insert(fileNameUser.index(i),i) # index is used to maintain the correct order from fileNameUser
    #lx.out('vars in filename:', foundMARI_vars)
    
    # If only the UDIM is in the filename template try
    # to extract it from the image filename
    if len(foundMARI_vars) == 1 and '$UDIM' in foundMARI_vars:
        
        # Extract the delimiters from filename template
        delimiter = fileNameUser.replace('$UDIM', '%3%').split('%3%')
        delimiter = filter(None, delimiter) # Delete empty strings

        # Find delimiter in the actual filename
        # Reformat the filename to a list
        for i in delimiter:
            if i in fileName:
                fileName = fileName.replace(i, '%3%')
        fileName = fileName.split('%3%')
        
        # Search filename list and look for a
        # four digit UDIM string and return it
        for string in fileName:
            try:
                int(string)
            except:
                pass
            else:
                if len(string) == 4:
                    return {foundMARI_vars[0][:4]:string}
    
    else:    
        ## Extract delimiter from the filename ##
        # All chars which are not within the MARI_vars are seen as delimiter
        # Returns a list of delimiters
        d = fileNameUser # $ENTITY-$CHANNEL.$UDIM
        d = re.split("\\" + "|\\".join(MARI_vars), d) # re.split uses regular expressions "\\" is used as escape character for "$": join -> "\$ENTITY|\$CHANNEL|\$UDIM" split -> ['','-','.','']
        d = filter(None, d) # Clean up list -> remove items which are empty e.g.: ''
        
        # Convert delimiter to regular expressions
        # re.escape: escapes all special character in string
        d = re.escape("|".join(d)).replace('\\|', '|') # convert '\|' -> '|' after re.escape
        #lx.out('d', d)
        
        # Extract the values of the foundMARI_vars from the actual filename
        fileVars = {}
        fileName = re.split(d, fileName)
        #lx.out('filename:', fileName)
        fileName = filter(None, fileName)
    
        for var in foundMARI_vars:
            fileVars[var[:4]] = fileName[foundMARI_vars.index(var)]
        return fileVars
    
    
def get_clipPath(selection): # Not used currently
    """Returns a dictionary. The key is the actual file path of the image map. Per key the current
    position number and the texture ID are saved."""
    list = {}
    for imap in selection:
        layerservice.select('texture.N', 'all')
        for number in range(layerservice.query('texture.N')):
            layerservice.select('texture.id', str(number))
            if layerservice.query('texture.id') == imap:
                list [layerservice.query('texture.clipFile')] = [number,imap]
    return list


def getUVoffSet(UDIM):
    """Converts UDIM to UVoff set values. A 4 digit number as UDIM must be given. e.g. 1012"""
    try:
        int(UDIM)
        U_offset = -(int(UDIM[3]) - 1)
        V_offset = -(int(UDIM[1:3]))
        return U_offset, V_offset
        
    except ValueError:
        lx.out("MARI ToolKit: No UDIM found.")
        return False

def filterClips(clipID, clip_size= 'w:8'):
    '''Delete a clip which has a given pixel size'''
    layerservice.select('clip.N', 'all')
    for num in xrange(layerservice.query('clip.N')):
        layerservice.select('clip.id', str(num))
        if clipID == layerservice.query('clip.id') and clip_size in layerservice.query('clip.info').split(' '):
            lx.eval('clip.delete')
            lx.out('8x8 clip deleted:', clipID)
       
    
def set_gamma(value):
    """Set gamma with given value for selected images."""
    sceneservice.select('selection', 'imageMap')
    selection = sceneservice.queryN('selection')
    if selection:
        for i in selection:
            lx.eval("item.channel imageMap$gamma %s" %value)
    else:
        lx.out("MARI ToolKit: nothing selected")
    

def vmap_selected(vmap_num, layer_index):
    """See if a UV map of the current layer is selected and returns the name.
    Also returns false if no vmaps are in scene"""

    if vmap_num == 0:
        return False
    
    else:
        for i in range(vmap_num):
            layerservice.select('vmap.layer', str(i))
            layerservice.select('vmap.type', str(i))
            vmap_layer = layerservice.query('vmap.layer') + 1 # Layer index starts at 1 and not at 0 -> +1 to shift index
            vmap_type = layerservice.query('vmap.type')
    
            if vmap_type == "texture" and vmap_layer == layer_index:
                layerservice.select('vmap.selected', str(i))
                if layerservice.query('vmap.selected') == True:
                    vmap_name = layerservice.query('vmap.name')
                    return vmap_name


def loadTextures(fileList, filter_clips, fileNameUser, UVmap_name):
    '''Load in textures from a file list. Filter 8x8 clips, save tags as metadata for clip and imageMap
    and set the UV offset to the UDIM value in the metadata.
    Returns Dictionary of created textures: {}'''

    # Clear Selection
    lx.eval('select.drop item')    
    
    # Setup tags from filename, create clip and then create tags for clip    
    clipList = {}
    for clipPath in fileList:
        try:
            tags = create_TagsFromFilename(fileNameUser, get_filename(clipPath))
        except:
            lx.out('There was a problem with the filename: ',get_filename(clipPath))
            continue
        
        tags[MTK_TYPE] = 'imageMap'
        
        # Load texture as clip
        lx.eval("clip.addStill %s" %clipPath)
        
        # Check clip size if delete 8x8 textures should be ignored
        if filter_clips == True:
            sceneservice.select('selection', 'videoStill')
            clipID = sceneservice.query('selection')            
            filterClips(clipID, clip_size='w:8')
        
        else:
            # create tags for item
            createTags(tags)

            # Save clipID with its tags
            sceneservice.select('selection', 'videoStill')
            clipList[sceneservice.query('selection')] = tags
    
    # Create the image maps from the clipList
    imageMaps = {}
    for clipName, clipTags in clipList.iteritems(): 
        imageMapID = create_imageMap(clipName, UVmap_name, getUVoffSet(clipTags[UDIM]))
        createTags(clipTags)
        imageMaps[imageMapID] = clipTags
    
    return imageMaps

def loadTextures2(fileList, filter_clips, fileNameUser, UVmap_name):
    '''Uses the new UDIM functionality introduced in modo 801. 
    Loads the textures into image folders in the clip browser. Sets the UDIM according to the filename.
    If channel and/or entity is specified in the filename template the folder name is $ENTITY_$CHANNEL.
    
    returns dict of created imagemaps'''
    
    # Clear Selection and walk through files
    lx.eval('select.drop item')    
    clipList = {}
    for clipPath in fileList:
        
        # Clear selection and scan for image folders
        lx.eval('select.drop item')
        imageFolders = getItemTags(item_type='imageFolder')

        # Extract tags from the filename
        try:
            tags = create_TagsFromFilename(fileNameUser, get_filename(clipPath))

        except:
            lx.out('There was a problem with the filename: ',get_filename(clipPath))
            continue

        else:
            # Tags for the image folder; UDIM is removed and MTK_TYPE added
            tags_folder = tags
            tags_folder.pop(UDIM, None)
            tags_folder[MTK_TYPE] = 'imageFolder'
            
            # Create image map and check clip size 
            # If filter_clips is active 8x8 textures are deleted
            tags[MTK_TYPE] = 'imageMap'
            lx.eval("clip.addStill %s" %clipPath)
            if filter_clips == True:
                sceneservice.select('selection', 'videoStill')
                clipID = sceneservice.query('selection')            
                filterClips(clipID, clip_size='w:8')
            
            else:
                # Set the UDIM value and attach tags to image
                lx.eval('clip.setUdimFromFilename')
                createTags(tags)
                
                # Get clipID
                sceneservice.select('selection', 'videoStill')
                clipID = sceneservice.query('selection')            
            
            # Create folder name from tags
            # If neither CHANNEL nor ENTITY is found the default name 'MTK IMPORT' is given
            if CHANNEL in tags_folder:
                if ENTITY in tags_folder:
                    imageFolder_name = tags_folder[ENTITY] + '_' + tags_folder[CHANNEL]
                else:
                    imageFolder_name = tags_folder[CHANNEL]
            elif CHANNEL not in tags_folder:
                if ENTITY in tags_folder:
                    imageFolder_name = tags_folder[ENTITY]
                else:
                    imageFolder_name = 'MTK IMPORT'
            
            # Find a matching image folder
            # If no folder is found image_folderID is None
            image_folderID = None
            for folder_id, folder_tag in imageFolders.iteritems():
                compare = set(folder_tag.values()) ^ set(tags_folder.values()) # len of zero -> its a match
                if len(compare) == 0:
                    image_folderID = folder_id
                    break
                else:
                    pass
            
            # Create new image folder
            if image_folderID == None:    
                lx.eval('clip.newFolder')
                
                createTags(tags_folder)
                lx.eval('clip.name {%s}' %imageFolder_name)
            
                sceneservice.select('selection', 'imageFolder')
                image_folderID = sceneservice.query('selection')
                new_imageFolder = True
            
            else:
                new_imageFolder = False
            
            # Move image under image folder
            # If a new folder was created save its id and tags into the clipList
            # -> only new folders create new imagemaps in the shadertree
            lx.eval('item.parent {%s} {%s} 0' %(clipID, image_folderID))
            if new_imageFolder == True:
                clipList[image_folderID] = tags_folder

    # Create image maps in Shader Tree and return all created maps as a dict
    imageMaps = {}
    for folderID, clipTags in clipList.iteritems():
        imageMapID = create_imageMapFromFolder(folderID, UVmap_name)
        createTags(clipTags)
        imageMaps[imageMapID] = clipTags
    
    return imageMaps


def renderID():
    """Return the render ID of the scene"""
    sceneservice.select("render.N", "all")
    itemNum = sceneservice.query("render.N")
    for i in range(itemNum):
        sceneservice.select("render.id", str(i))
        return sceneservice.query("item.id")
    

def get_UDIMSets(meshIDs):
    """Return a dict of UDIM selection sets per mesh. A list of meshIDs must be given.
    {'mesh':['UDIM1','UDIM2']}"""
    
    # Clear selection
    lx.eval('select.drop item mesh') 
    
    # Go through the mesh items and save all UDIM selection sets in data
    data = {}
    for mesh in meshIDs:
        lx.eval('select.subItem {0} set mesh'.format(mesh))
        polysetNum = layerservice.query('polset.N')
        for i in range(polysetNum):
            layerservice.select("polset.name", str(i))
            polySetName = layerservice.query("polset.name")
            if "UDIM" in polySetName:
                try:
                    data[mesh].append(polySetName)
                except:
                    data[mesh] = [polySetName]
            
    lx.eval('select.drop item mesh')
    
    return data


def create_mask_ENTITY(parent, tags, name=None):
    '''Create mask for ENTITY and return its mask.id'''
    lx.eval("shader.create mask")
    
    sceneservice.select('selection', 'mask')
    maskID = sceneservice.query('selection')
    
    lx.eval("texture.parent %s 1" %parent)
    createTags(tags)
    lx.eval('item.tag string $MTK ENTITY_mask')
    lx.eval('item.name {%s} mask' %tags)
    
    if name:
        lx.eval('item.name {%s} mask' %name)

    return maskID
 
    
def create_mask_UDIM(parent, tags, selection_set, createMat=True):
    '''Create mask for UDIM and return its mask.id.
    sets the PTag to a selection set'''
    lx.eval("shader.create mask")

    sceneservice.select('selection', 'mask')
    maskID = sceneservice.query('selection')
    
    lx.eval("texture.parent %s 0" %parent)
    createTags(tags)
    lx.eval('item.tag string $MTK UDIM_mask')
    lx.eval("mask.setPTagType {Selection Set}")
    lx.eval("mask.setPTag {%s}" %selection_set)
    
    # create material in created group
    if createMat == True:
        lx.eval("shader.create advancedMaterial")
        createTags(tags)

    return maskID


def create_missing_entityGrps(imageItemList):    
    '''Scans for entity mask groups in the shader tree.
    If a group is missing it is created.'''
    present_entityIDs = scan_masks('ENTITY_IDs')
    if '$ENTITY' in fileNameUser:
        imported_images = {}
        for image, imageTag in imageItemList.iteritems():
            try:
                imported_images[imageTag[ENTITY]].append(image)
            except:
                imported_images[imageTag[ENTITY]] = [image]
        
        lx.out('imported images: ',imported_images)
        
        created = []
        for entity, imageID in imported_images.iteritems():
            if entity not in (present_entityIDs.keys() or created):
                lx.eval('select.drop item')
                new_entity = create_mask_ENTITY(renderID(), {'$ENTITY':entity}, name=entity)
                created.append(new_entity)
            else:
                continue


def createTags(dictionary):
    '''Create custom tags for a selected item. A dictionary with the tag values must be given.
    {'UDIM':'1011','ENTITY':'Mesh',...}'''
    for key, value in dictionary.iteritems():
        lx.eval('item.tag string {%s} {%s}' %(key[:4], value)) # key value must be only 4 chars long

def move2entityMasks(images, masks):
    """Move images into their entity mask groups"""
    for imageID, imageTag in images.iteritems():
        try:
            entity = imageTag[ENTITY]
        except:
            continue
        else:
            for maskID, maskTags in masks.iteritems():
                if maskTags[MTK_TYPE] == 'ENTITY_mask' and maskTags[ENTITY] == entity:
                    lx.eval('select.item %s' %imageID)
                    lx.eval('texture.parent %s -1' %maskID)                    

def moveImageMaps(images, masks):
    '''Move image maps to their UDIM_mask. Expects two dicts: {item.id:{tags}}'''
    for imageID, imageTag in images.iteritems():
        try:
            ENTITY_val = imageTag[ENTITY]
        except:
            ENTITY_val = False
        
        # If a ENTITY is in the imageTags find the correct UDIM_mask underneath the ENTITY_mask and move image there
        if ENTITY_val != False:
            UDIM_val = imageTag[UDIM]
            for maskID, tags in masks.iteritems():
                if tags[MTK_TYPE] == 'UDIM_mask' and tags[UDIM] == UDIM_val and tags[ENTITY] == ENTITY_val:
                    lx.eval('select.item %s' %imageID)
                    lx.eval('texture.parent %s -1' %maskID)

        # Where no ENTITY_mask is found image is moved to the nearest UDIM_mask which matches
        else:
            UDIM_val = imageTag[UDIM]
            for maskID, tags in masks.iteritems():
                if tags[MTK_TYPE] == 'UDIM_mask' and tags[UDIM] == UDIM_val:
                    lx.eval('select.item %s' %imageID)
                    lx.eval('texture.parent %s -1' %maskID)   



def check_UDIMSelSets(meshIDs):
    """Check if selection sets are already created for the selected mesh item."""
    if not get_UDIMSets(meshIDs):
        try:
            dialog_yesNo('There are no UDIM selection sets. Should I create them? This could take a while. So maybe you grab a coffe.')
            for mesh in meshIDs:
                lx.eval('select.subItem %s set mesh' %mesh)
                lx.eval("@UV_tools.py create_selSets")
        except:
            return False
    else:
        lx.out("MARI ToolKit: UDIM selection sets existing.")
        pass

def scanClips():
    """Scan the scene for all clips and return a list"""
    sceneservice.select("clip.N", "all")
    data = []
    for i in range(sceneservice.query("clip.N")):
        sceneservice.select("clip.id", str(i))
        data.append(sceneservice.query("clip.id"))
    return data
    
def setShaderEffect(imageItemList=None):
    """Set the shader effect of imported textures.
    Textures must have the $CHANNEL tag set as metadata and the user values of $CHANNELS must be set correctly.
    Three modes:
    - Modify selection in shader tree
    - No selection -> modify all
    - Modify given imageMap item list -> optional
    
    Following effects are supported:
    diffColor
    specAmount
    reflAmount
    bump
    displace
    normal.
    """
    # $CHANNEL user values
    chan_diff = lx.eval("user.value MARI_TOOLS_CHAN_diff ?")
    chan_spec = lx.eval("user.value MARI_TOOLS_CHAN_spec ?")
    chan_refl = lx.eval("user.value MARI_TOOLS_CHAN_refl ?")
    chan_bump = lx.eval("user.value MARI_TOOLS_CHAN_bump ?")
    chan_dspl = lx.eval("user.value MARI_TOOLS_CHAN_displ ?")
    chan_nrml = lx.eval("user.value MARI_TOOLS_CHAN_normal ?")
    
    # Mapping from user values to shader effects #
    chan_values = {chan_diff:"diffColor",
                   chan_spec:"specAmount",
                   chan_refl:"reflAmount",
                   chan_bump:"bump",
                   chan_dspl:"displace",
                   chan_nrml:"normal"
                   }
    
    sceneservice.select("selection", "imageMap")
    selection = sceneservice.queryN("selection")
    
    if selection and imageItemList is None:
        itemList = getItemTags('imageMap')
        
        # remove not found items
        for imageID, value in getItemTags('imageMap').iteritems():
            if imageID not in selection:
                del itemList[imageID]
        
    elif imageItemList is None and not selection:
        itemList = getItemTags('imageMap')
    
    elif imageItemList is not None:
        itemList = imageItemList
    
    for imageID, tags in itemList.iteritems():
        try:
            chan_image = tags[CHANNEL]
        except:
            continue
        
        sceneservice.select("item.type", str(imageID))
        if chan_image in chan_values:
            lx.eval("select.subItem {%s} set textureLayer" %imageID)
            lx.eval("shader.setEffect {%s}" %chan_values[chan_image])
     
            
def getImageMaps(clip_list):
    """From Matt Cox. Returns a list of all the clips which are used in the shader tree.
    returns only the name of the clip not the extension."""
    images = []
    
    for clip_obj in clip_list:
        
        try:
            scn_svc = lx.service.Scene ()
            
            clip_type = scn_svc.ItemTypeLookup (lx.symbol.sITYPE_VIDEOSTILL)
            image_type = scn_svc.ItemTypeLookup (lx.symbol.sITYPE_IMAGEMAP)
            
            scene = lxu.select.SceneSelection().current()
            graph = lx.object.ItemGraph (scene.GraphLookup (lx.symbol.sGRAPH_SHADELOC))
            
            if isinstance (clip_obj, str) == True:
                clip = scene.ItemLookupIdent (clip_obj)
            else:
                clip = lx.object.Item (clip_obj)
                    
            if clip.TestType (clip_type) == False:
                return []
            
            count = graph.RevCount (clip)
            
            for i in range (count):
                image = graph.RevByIndex (clip, i)
                if image.TestType (image_type) == True:
                    images.append (get_filename(clip_obj.split(";")[0]))
                    
        except:
            pass
            
    return images

        
def get_shaderTreeIndex(parent, item):
    '''Return order index number of a item in the shadertree.
    Use type description as returned from MODO'''
    sceneservice.select('item', parent)
    childList = list(sceneservice.query('item.children'))
    try:
        return childList.index(item)
    except:
        pass

def sortST(selection, item_type):
    '''Sort specific shader tree items alphabetically. Structure is maintained.'''
    # Check if something is selected
    if selection and len(selection) > 0:    
        # Look up exposed item names and sort them in alphabetic order
        itemList = []
        for item in selection:
            sceneservice.select('item', item)
            itemList.append(sceneservice.query('item.name'))
        itemList = sorted(itemList, key=str.lower)
        lx.out(itemList)
        # Check the item type and find the items position in shader tree
        # Dict structure: {parent:[[indices],[items]]}
        data = {}
        for item in itemList:
            lx.out(data)
            lx.out('------------')
            lx.out('item.id', item)
            itemID = lx.eval('query sceneservice item.id ? {%s}' %item)
            sceneservice.select('item.type', itemID)
            if sceneservice.query('item.type') == item_type:
                lx.out(itemID)
                parent = sceneservice.query('item.parent')
                try:
                    data[parent][0].append(get_shaderTreeIndex(parent, itemID))
                    data[parent][1].append(item)
                except:
                    data[parent] = [[get_shaderTreeIndex(parent, itemID)],[itemID]]
        lx.out(data)        
        # Sort the items in the shader tree
        for parent, value in data.iteritems():
            bottomItem = (min(value[0]))
            itemList = value[1]
            for item in itemList:
                lx.eval('select.item {%s}' %(item))
                lx.eval('texture.parent {%s} {%s}' %(parent, bottomItem))
    else:
        lx.out('Nothing selected or wrong type defined')

    
def getItemTags(item_type='all', selection=None):
    '''Find item tags in scene created from the MARI Tool Kit. Default: all items are searched. A selection can also be given
    Returns {item.id{tagType:tag,}}'''
    # {item.id:{ENTITY:name,UDIM:1001,CHANNEL:diffuse}}
    data = {}
    if selection:
        lx.out('selection: ',selection)
        if isinstance(selection, str) == True:
            selection = [selection]
        for i in selection:            
            sceneservice.select('item.id', str(i))
            itemID = sceneservice.query('item.id')
            try:
                itemTagTypes = sceneservice.queryN('item.tagTypes')
                itemTags = sceneservice.queryN('item.tags')
                if '$MTK' in itemTagTypes:
                    data[itemID] = dict(zip(itemTagTypes, itemTags))
            except:
                pass

    else:
        sceneservice.select('item.N', 'all')
        item_num = sceneservice.query('item.N')
        for item in xrange(item_num):
            sceneservice.select('item.id', str(item))
            itemID = sceneservice.query('item.id')
            if sceneservice.query('item.type') == item_type or item_type == 'all':
                try:
                    itemTagTypes = sceneservice.queryN('item.tagTypes')
                    itemTags = sceneservice.queryN('item.tags')
                    if '$MTK' in itemTagTypes:
                        data[itemID] = dict(zip(itemTagTypes, itemTags))
                except:
                    pass
    return data


def scan_masks(mode):
    '''Returns a dict {entity:[maskid1,maskid2,...],...}.
    Args:
    ENTITY_UDIMs: {entity:[udim1, udim2]}
    ENTITY_IDs: {entity:'mask01',entity:'mask02}
    UDIM_IDs: {udim:[mesh1,mesh2,...]}'''

    data={}
    
    # Create list with entities and all udims underneath them
    if mode == 'ENTITY_UDIMs':
        sceneservice.select('mask.N', 'all')
        for num in xrange(sceneservice.query('mask.N')):
            sceneservice.select('mask.id', str(num))
            maskID = sceneservice.query('mask.id')
            tagTypes = sceneservice.queryN('mask.tagTypes')
            tagValues = sceneservice.queryN('mask.tags')

            if (UDIM and ENTITY) in tagTypes and 'UDIM_mask' in tagValues:
                temp = dict(zip(tagTypes, tagValues))                
                try:
                    data[temp[ENTITY]][temp[UDIM]] = maskID
                except:
                    data[temp[ENTITY]] = {temp[UDIM]:maskID}

        return data

    # Create list with entity names and all the mask ids
    elif mode == 'ENTITY_IDs':
        sceneservice.select('mask.N', 'all')
        for num in xrange(sceneservice.query('mask.N')):
            sceneservice.select('mask.id', str(num))
            maskID = sceneservice.query('mask.id')
            tagTypes = sceneservice.queryN('mask.tagTypes')
            tagValues = sceneservice.queryN('mask.tags')
            
            if ENTITY in tagTypes and 'ENTITY_mask' in tagValues:
                temp = dict(zip(tagTypes, tagValues))                
                data[temp[ENTITY]] = maskID
    
        return data
    
    elif mode == 'UDIM_IDs':
        sceneservice.select('mask.N', 'all')
        for num in xrange(sceneservice.query('mask.N')):
            sceneservice.select('mask.id', str(num))
            maskID = sceneservice.query('mask.id')
            tagTypes = sceneservice.queryN('mask.tagTypes')
            tagValues = sceneservice.queryN('mask.tags')
            
            if UDIM in tagTypes and 'UDIM_mask' in tagValues:
                temp = dict(zip(tagTypes, tagValues))                
                data[temp[UDIM]] = maskID

        return data
                

##------------ DIALOGS & MESSAGES -----------##
def warning_msg(name):
    """A modal warning dialog. Message text can be set through name var."""
    try:
        lx.eval("dialog.setup warning")
        lx.eval("dialog.title {Error}")
        lx.eval("dialog.msg {Ooopsy. %s.}" %name)
        lx.eval("dialog.result ok")
        lx.eval("dialog.open")
        
    except RuntimeError:
        pass

def dialog_yesNo(header, text):
    try:
        lx.eval("dialog.setup yesNo")
        lx.eval("dialog.title {%s}" %header)
        lx.eval("dialog.msg {%s}" %text)
        lx.eval("dialog.result ok")
        lx.eval("dialog.open")
        
        lx.eval("dialog.result ?")
        return True
    
    except RuntimeError:
        return False
    

def dialog_brake():
    try:
        lx.eval("dialog.setup yesNo")
        lx.eval("dialog.title {Coffee Brake?}")
        lx.eval("dialog.msg {This could take a while. Do you want to grab a cup of coffee?}")
        lx.eval("dialog.result ok")
        lx.eval("dialog.open")
        
        lx.eval("dialog.result ?")
        return True
    
    except RuntimeError:
        return False

###---------------METHODS END --------------------------###


## MODO SERVICES ##
layerservice = lx.Service("layerservice")
sceneservice = lx.Service("sceneservice")

## TAG TYPE VALUES ##
MTK_TYPE = '$MTK' # Type description: ENTITY_mask, UDIM_mask, imageMap
ENTITY = '$ENT'
UDIM = '$UDI'
CHANNEL = '$CHA'

## VARIABLES ##
args = lx.args()[0] # Arguments. Only the first argument is passed.
maskColorTag = "none" # Color tag for UDIM mask groups

## Store Layer index and vmaps ##
layerservice.select('layer.id','main')
layer_index = layerservice.query('layer.index') #select the current mesh layer
layerservice.select('vmap.N', 'all')
vmap_num = layerservice.query('vmap.N') # Number of vertex maps of selected mesh


#################################
#           USER VALUES         #
#################################
gamma_correction = lx.eval("user.value MARI_TOOLS_gamma ?") # Gamma correction on/off
gamma_value = lx.eval("user.value MARI_TOOLS_gammavalue ?") # Gamma value from UI
fileNameUser = lx.eval("user.value MARI_TOOLS_filename ?") # Filename structure
filter_clips = lx.eval("user.value MARI_TOOLS_filter_clips ?") # Delete 8x8 clips on/off
create_maskGroups = lx.eval("user.value MARI_TOOLS_create_maskGroups ?") # create missing UDIM mask groups on/off


######################################
#            ARGUMENTS               #
######################################

# Import & organize textures into groups #
if args == "organizeLoadFiles2":
    
    ##############################
    #      IMPORT TEXTURES       #
    ##############################
    
    sceneservice.select('selection', 'mesh')
    mesh_items = sceneservice.queryN('selection')
    entity_status = '$ENTITY' in fileNameUser
    
    ## Check the selection ##
    ## if nothing is selected all mesh items are stored in a dict if $ENTITY is specified.
    try:
        mesh_items[0]
        selection_status = True
    except:
        selection_status = False
        
        # Future enhancement walk through all meshes which match the ENTITY
        #mesh_items = {}
        #if entity_status == True:
            #sceneservice.select('mesh.N', 'all')
            #for i in range(sceneservice.query('mesh.N')):
                #sceneservice.select('mesh.id', str(i))
                #mesh_items[sceneservice.query('mesh.name')] = sceneservice.query('mesh.id')            
    
    ## CHECK SETTINGS ##        
    if "$UDIM" not in fileNameUser:
        warning_msg("UDIM is missing in the filename template.")
    
    ## Warning if UV set is selected ##
    elif vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    ## Warning if nothing is selected and no ENTITY is defined ##
    elif selection_status == False: #and entity_status == False:
        warning_msg("Please Select an appropriate mesh layer.")
    
    else:
        UVmap_name = vmap_selected(vmap_num, layer_index)        
        
        # Open dialog to load image files
        fileList = load_files() 
        
        # Load the textures and create image maps in shader tree
        imageItemList = loadTextures2(fileList, filter_clips, fileNameUser, UVmap_name)
     
        if imageItemList:
            
            # Check if the selection sets are created
            check_UDIMSelSets(mesh_items)
            
            # Clear selection
            lx.eval('select.drop item')
            
            # Find present mask groups in shadertree
            # And create missing groups for imported images
            create_missing_entityGrps(imageItemList) 
            
            # Sort the images into their masks and change the shader effect
            move2entityMasks(imageItemList, getItemTags('mask'))                        
            
            if CHANNEL in fileNameUser:
                setShaderEffect(imageItemList)
            else:
                pass
            
            # Select imported images
            lx.eval('select.drop item')
            for i in imageItemList.keys():
                lx.eval('select.subItem {0} add textureLayer'.format(i))
        
            if gamma_correction == True:
                set_gamma(gamma_value)            


## Old import 701 ##
# Import & organize textures into groups #
if args == "organizeLoadFiles":
    
    ##############################
    #      IMPORT TEXTURES       #
    ##############################
    
    sceneservice.select('selection', 'mesh')
    mesh_items = sceneservice.queryN('selection')
    entity_status = '$ENTITY' in fileNameUser
    
    ## Check the selection ##
    ## if nothing is selected all mesh items are stored in a dict if $ENTITY is specified.
    try:
        mesh_items[0]
        selection_status = True
    except:
        selection_status = False
        
        # Future enhancement walk through all meshes which match the ENTITY
        #mesh_items = {}
        #if entity_status == True:
            #sceneservice.select('mesh.N', 'all')
            #for i in range(sceneservice.query('mesh.N')):
                #sceneservice.select('mesh.id', str(i))
                #mesh_items[sceneservice.query('mesh.name')] = sceneservice.query('mesh.id')            
    
    ## CHECK SETTINGS ##        
    if "$UDIM" not in fileNameUser:
        warning_msg("UDIM is missing in the filename template.")
    
    ## Warning if UV set is selected ##
    elif vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    ## Warning if nothing is selected and no ENTITY is defined ##
    elif selection_status == False: #and entity_status == False:
        warning_msg("Please Select an appropriate mesh layer.")
    
    else:
        UVmap_name = vmap_selected(vmap_num, layer_index)        
        
        # Open dialog to load image files
        fileList = load_files() 
        
        # Load the textures and create image maps in shader tree
        imageItemList = loadTextures(fileList, filter_clips, fileNameUser, UVmap_name)
    
    
        if imageItemList:
            
            ## Check if the selection sets are created##
            check_UDIMSelSets(mesh_items)
            
            # Clear selection
            lx.eval('select.drop item')
            
            # Check/create ENTITY and UDIM mask groups
            # Two cases:
            # - $ENTITY is defined in filename template
            # - No entity -> only UDIM mask are created 
            if '$ENTITY' in fileNameUser:
                # Save entity with its udims for all imported images
                # {entity:[udim,udim,...]}
                imported_images = {}
                for image, imageTag in imageItemList.iteritems():
                    try:
                        imported_images[imageTag[ENTITY]].append(imageTag[UDIM])
                    except:
                        imported_images[imageTag[ENTITY]] = [imageTag[UDIM]]


                # Scan the scene for any entity groups
                present_masks = scan_masks('ENTITY_UDIMs')
                present_entityIDs = scan_masks('ENTITY_IDs')

                # Go through all imported images and their entity entries
                # If there are entity masks in the shader tree we check each udim if it has already a mask in the shader tree
                # If not it is created and moved underneath its entity
                # To stop recursion we save its udim value in the created list so images with same udim and entity don't create double entries
                # If there are entity masks in the shader tree we create those
                for entity_name, udim_list in imported_images.iteritems():
                    created = [] # list for all new created groups
                    if present_entityIDs and entity_name in present_entityIDs.keys():
                        lx.out('already in scene:', present_masks[entity_name].keys())
                        for udim in udim_list:
                            lx.out('------------------------')
                            lx.out('UDIM:', udim)
                            lx.eval('select.drop item')
                            if udim not in created and udim not in present_masks[entity_name].keys():
                                lx.out('created %s in %s' %(udim, entity_name))
                                create_mask_UDIM(present_entityIDs[entity_name], {'$UDIM':udim,'$ENTITY':entity_name}, '$UDIM:'+ udim, createMat=True)
                                created.append(udim) # store new created group
                            else:
                                pass
                            lx.out('------------------------')
                    else:
                        lx.eval('select.drop item')
                        new_entity = create_mask_ENTITY(renderID(), {'$ENTITY':entity_name}, name=entity_name)
                        for udim in udim_list:
                            lx.out('------------------------')
                            lx.out('UDIM:', udim)
                            lx.eval('select.drop item')
                            if udim not in created: #and udim not in present_masks[entity_name].keys():
                                lx.out('created %s in %s' %(udim, entity_name))
                                create_mask_UDIM(new_entity, {'$UDIM':udim,'$ENTITY':entity_name}, '$UDIM:'+ udim, createMat=True)
                                created.append(udim) # store new created group
                            else:
                                pass
                            lx.out('------------------------')
                            
            else:
                # Create UDIM mask if these are not in the Shader tree
                lx.out(imageItemList)
                present_udims = scan_masks('UDIM_IDs')
                created = []
                for image in imageItemList.values():
                    udim_val = image[UDIM]
                    if udim_val not in created and udim_val not in present_udims.keys():
                        create_mask_UDIM(renderID(), {'$UDIM':udim_val}, '$UDIM:'+ udim, createMat=True)
                        created.append(udim_val)
                            
            # Sort the images into their masks and change the shader effect
            moveImageMaps(imageItemList, getItemTags('mask'))                        
            if CHANNEL in fileNameUser:
                setShaderEffect(imageItemList)
            else:
                pass
    
# Import only textures strait into the shader tree root #
elif args == "loadFiles":
    sceneservice.select('selection', 'mesh')

    if "$UDIM" not in fileNameUser:
        warning_msg("UDIM is missing in the filename template.")
    
    # Check if a UV set is selected
    elif vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    else:
        UVmap_name = vmap_selected(vmap_num, layer_index)
        fileList = load_files() # Open dialog to load image files
        
        if fileList:
            loadTextures(fileList, filter_clips, fileNameUser, UVmap_name)
        else:
            lx.out("MARI ToolKit: Canceld by user.")


### ----------- ####

#####################
#       TOOLS       #
#####################

# Sort into material groups modo 801
elif args == "sortToGroups2":
    
    # Query selection
    sceneservice.select('selection', 'imageMap')
    imageMaps = sceneservice.query('selection')
    
    imageItemList = getItemTags(selection=imageMaps)
    
    if create_maskGroups == True:
        # Create missing mask groups and sort image maps into groups
        create_missing_entityGrps(imageItemList)                
        move2entityMasks(imageItemList, getItemTags('mask'))          
        
    else:
        move2entityMasks(imageItemList, getItemTags('mask'))
    


# Sort into material groups modo 701
elif args == "sortToGroups":
    
    # Query selection
    sceneservice.select('selection', 'imageMap')
    imageMaps = sceneservice.query('selection')
    
    imageItemList = getItemTags(selection=imageMaps)
    
    if create_maskGroups == True:
        
        # Check/create ENTITY and UDIM mask groups
        # Two cases:
        # - $ENTITY is defined in filename template
        # - No entity -> only UDIM mask are created 
        if '$ENTITY' in fileNameUser:
            # Save entity with its udims for all imported images
            # {entity:[udim,udim,...]}
            selected_imageMaps = {}
            for image, imageTag in imageItemList.iteritems():
                try:
                    selected_imageMaps[imageTag[ENTITY]].append(imageTag[UDIM])
                except:
                    selected_imageMaps[imageTag[ENTITY]] = [imageTag[UDIM]]
    
    
            # Scan the scene for any entity groups
            present_masks = scan_masks('ENTITY_UDIMs')
            present_entityIDs = scan_masks('ENTITY_IDs')
    
            # Go through all imported images and their entity entries
            # If there are entity masks in the shader tree we check each udim if it has already a mask in the shader tree
            # If not it is created and moved underneath its entity
            # To stop recursion we save its udim value in the created list so images with same udim and entity don't create double entries
            # If there are entity masks in the shader tree we create those
            for entity_name, udim_list in selected_imageMaps.iteritems():
                created = [] # list for all new created groups
                if present_entityIDs and entity_name in present_entityIDs.keys():
                    lx.out('already in scene:', present_masks[entity_name].keys())
                    for udim in udim_list:
                        lx.out('------------------------')
                        lx.out('UDIM:', udim)
                        lx.eval('select.drop item')
                        if udim not in created and udim not in present_masks[entity_name].keys():
                            lx.out('created %s in %s' %(udim, entity_name))
                            create_mask_UDIM(present_entityIDs[entity_name], {'$UDIM':udim,'$ENTITY':entity_name}, '$UDIM:'+ udim, createMat=True)
                            created.append(udim) # store new created group
                        else:
                            pass
                        lx.out('------------------------')
                else:
                    lx.eval('select.drop item')
                    new_entity = create_mask_ENTITY(renderID(), {'$ENTITY':entity_name}, name=entity_name)
                    for udim in udim_list:
                        lx.out('------------------------')
                        lx.out('UDIM:', udim)
                        lx.eval('select.drop item')
                        if udim not in created: #and udim not in present_masks[entity_name].keys():
                            lx.out('created %s in %s' %(udim, entity_name))
                            create_mask_UDIM(new_entity, {'$UDIM':udim,'$ENTITY':entity_name}, '$UDIM:'+ udim, createMat=True)
                            created.append(udim) # store new created group
                        else:
                            pass
                        lx.out('------------------------')
                        
        else:
            # Create UDIM mask if these are not in the Shader tree
            lx.out(imageItemList)
            present_udims = scan_masks('UDIM_IDs')
            created = []
            for image in imageItemList.values():
                udim_val = image[UDIM]
                if udim_val not in created and udim_val not in present_udims.keys():
                    create_mask_UDIM(renderID(), {'$UDIM':udim_val}, '$UDIM:'+ udim, createMat=True)
                    created.append(udim_val)
                        
        # Sort the images into their masks and change the shader effect
        moveImageMaps(imageItemList, getItemTags('mask'))          
        
        
    else:
        moveImageMaps(imageItemList, getItemTags('mask'))

# Gamma Correction: Correct Gamma of textures 1.0/2.2 = 0.4546 #
elif args == "gammaCorrect":
    set_gamma(gamma_value)


# set the UVoffset according to $UDIM in comment tag #
elif args == "setUVoffset":
    sceneservice.select('selection', 'imageMap')
    selection = sceneservice.queryN('selection')    
    
    imageTags = getItemTags(selection=selection)
    lx.out(imageTags)
    
    # Check the selected imageMaps if any Tags are present.
    # If not those are created
    for imageMap in selection:
        if imageMap not in imageTags:
            layerservice.select('texture.N', 'all')
            for i in xrange(layerservice.query('texture.N')):
                layerservice.select('texture.id', str(i))
                if layerservice.query('texture.id') == imageMap:
                    filePath = layerservice.query('texture.clipFile')
                    lx.eval('select.item %s set' %imageMap)
                    newTags = create_TagsFromFilename(fileNameUser, get_filename(filePath))
                    newTags[MTK_TYPE] = 'imageMap'
                    createTags(newTags)
                    break
                else:
                    pass
        else:
            pass
    
    # After check the tags we can set the UVoffset for the selected textures
    imageTags = getItemTags('imageMap')
    lx.eval('select.drop item')
    lx.out(imageTags)
    for imap in selection:    
        if imap in imageTags.keys():
            lx.eval('select.item %s set' %imap)
            txtrLoc = lx.eval("texture.setLocator {%s} ?" %imap)
            UDIM_val = imageTags[imap][UDIM]
            lx.eval("select.subItem {%s} set" %txtrLoc)
            lx.eval("item.channel txtrLocator$m02 %s" %getUVoffSet(UDIM_val)[0])
            lx.eval("item.channel txtrLocator$m12 %s" %getUVoffSet(UDIM_val)[1])                
            lx.eval("item.channel txtrLocator$tileU reset")
            lx.eval("item.channel txtrLocator$tileV reset")
            

# Sort selected images top to bottom #
elif args == "sortImages":
    sceneservice.select('selection', 'imageMap')
    selection = sceneservice.query('selection')
    sortST(selection, 'imageMap')

# Create poly selection set for each UDIM #
elif args == "createPolySets":
    # Check if a UV map is selected
    if vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    # Proceed with UV_tools.py script
    elif dialog_brake() == True:
        sceneservice.select('selection', 'mesh')
        selection = sceneservice.queryN('selection')
        if selection:
            for mesh in selection:
                lx.eval('select.subItem %s set mesh' %mesh)
                lx.eval("@UV_tools.py create_selSets")
        else:
            warning_msg("Please select a least one mesh")    

# fixes UVs which lie directly on a UDIM border #
elif args == "fixUVs":
    # Check if a UV map is selected
    if vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    # Proceed with UV_tools.py script
    elif dialog_brake() == True:
        lx.eval("@UV_tools.py fix_uvs")
        
elif args == "setShaderEffect":
    setShaderEffect()

elif args == 'createMetaData':
    try:
        lx.eval('user.value MARI_TOOLS_filename')

    except:
        lx.out('user pressed cancel')

    else:    
        sceneservice.select('selection', 'imageMap')
        selection = sceneservice.queryN('selection')    
        
        imageTags = getItemTags(selection=selection)
        lx.out(imageTags)
        
        # Check the selected imageMaps if any Tags are present.
        # If not those are created
        for imageMap in selection:
            if imageMap not in imageTags:
                layerservice.select('texture.N', 'all')
                for i in xrange(layerservice.query('texture.N')):
                    layerservice.select('texture.id', str(i))
                    if layerservice.query('texture.id') == imageMap:
                        filePath = layerservice.query('texture.clipFile')
                        lx.eval('select.item %s set' %imageMap)
                        newTags = create_TagsFromFilename(fileNameUser, get_filename(filePath))
                        newTags[MTK_TYPE] = 'imageMap'
                        createTags(newTags)
                        break
                    else:
                        pass
            else:
                pass    
    

elif args == "testing":
    lx.out("-----TESTING-----")
    



