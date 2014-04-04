#python

"""
MARI TOOLs
Bjoern Siegert aka nicelife

Last edited 2014-03-27

Arguments:
loadFiles, gammaCorrect, setUVoffset, sortSelection, createPolySets

Import textures from MARI and some tools to manage these:
For import the user can choose:
- a delimiter so that the script can find the UDIM number
- to ignore the 8x8 pixel textures from import
- if the textures should be gamma corrected

Tools:
- Sets the UV offset automatically from the file name
- Gamma correction of imported texutres if needed
- Sort the images in scene tree in alphabetic order
- Create polygon sets for each UDIM


Version History:
v1.3
METADATA now storred in the imported textures:
If filename contains MARI filname variables ($ENTITY, $CHANNEL, $UDIM, $LAYER, $FRAME, $NUMBER, $COUNT, $[METADATA VALUE]) these are storred
as a comment tag of the texture. E.g.:
$UDIM:1001;$CHANNEL:diffuse

$CHANNEL options:
User can set values for diffuse color, specular amount, reflection amount, bump, normal and displacement

Filename template is now used to extract all the MARI filename variables and follows its same values

Imported textures can now be sorted into group masks in the shader tree and if $CHANNEL is set the shader effect is set as well
Grouping and shader effect are also tools.


v1.2
New Feature:
- Create selection sets for the different UDIMs

v1.1
Bugfixes:
- Creating the image maps didn't work reliable because of a selection in the shader tree. Clears selection (only select the Mesh) before creating the image maps now
- Sorting fixed
- Added some logging
"""

import re
import lx
import lxu.select

### METHODS ####

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

def create_imageMap(clipPath):
    """
    Create material in shader tree. Change it to an image map and set up UV projection type and tiling
    """    
    lx.eval("clip.addStill %s" %clipPath)
    lx.eval("shader.create constant")
    lx.eval("item.setType imageMap textureLayer")
    lx.eval("texture.setIMap {%s}" %get_filename(clipPath))
    lx.eval("item.channel imageMap$aa false")
    lx.eval("item.channel txtrLocator$projType uv")
    lx.eval("item.channel txtrLocator$tileU reset")
    lx.eval("item.channel txtrLocator$tileV reset")
    
    
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


def parseFileName(fileNameUser, fileName):    
    """Extract MARI variables from filename (without extension).
    Returns a dictionary with all found variables and their values:
    {'$CHANNEL':'diffuse','$UDIM':'1002'}"""
    
    # MARI filename variables
    MARI_vars = ["$ENTITY", "$CHANNEL", "$UDIM", "$LAYER", "$FRAME", "$NUMBER", "$COUNT", "$[METADATA VALUE]"]
    
    foundMARI_vars = []
    for i in MARI_vars:
        if i in fileNameUser:
            foundMARI_vars.insert(fileNameUser.index(i),i) # index is used to maintain the correct order from fileNameUser
    #lx.out('vars in filename:', foundMARI_vars)
    
    ## Extract delimiter from the filename ##
    # All chars which are not within the MARI_vars are seen as delimiter
    # Returns a list of delimiters
    d = fileNameUser # %ENTITY-%CHANNEL.$UDIM
    d = re.split("\\" + "|\\".join(MARI_vars), d) # re.split uses regular expressions "\\" is used as escape character for "$": join -> "\$ENTITY|\$CHANNEL|\$UDIM" split -> ['','-','.','']
    d = filter(None, d) # Clean up list -> remove items which are empty e.g.: ''
    
    # Convert delimiter to regular expressions
    # re.escape: escapes all special character in string
    d = re.escape("|".join(d)).replace('\\|', '|') # convert '\|' -> '|' after re.escape
    
    # Extract the values of the foundMARI_vars from the actual filename
    fileVars = {}
    fileName = re.split(d, fileName)
    fileName = filter(None, fileName)

    for var in foundMARI_vars:
        fileVars[var] = fileName[foundMARI_vars.index(var)]
    
    return fileVars
    
    
    
def get_clipPath(selection):
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
        
    
def check_clip_size(clip_name):
    """Checks the size of a clip and return True if it is 8x8 pixels"""
    
    clip_size = "w:8"
    layerservice.select('clip.N', 'all')
    for i in xrange(layerservice.query('clip.N')):
        layerservice.select('clip.id', str(i))
        if layerservice.query('clip.id') == clip_name:
            clip_info = layerservice.query('clip.info').split(' ')
            
            if clip_size in clip_info[1]: 
                lx.out("MARI ToolKit: %s deleted" %clip_name)
                return True
            else:
                return False


def set_gamma(value):
    """Set gamma with given value for selected images."""
    sceneservice.select('selection', 'imageMap')
    if not sceneservice.query('selection'):
        lx.out("MARI ToolKit: nothing selected")
    else:
        lx.eval("item.channel imageMap$gamma %s" %value)


def get_texture_parent(item_ID):
    """Returns the parent of an image map"""
    sceneservice.select('textureLayer', str(item_ID))
    return sceneservice.query('textureLayer.parent')


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


def createTextures(UVmap_name, fileList, gamma_correction, gamma_value):
    """Import and create textures in the shader tree.
    MARI filename variables are saved as comment tag, e.g. $ENTITY:Mesh;$CHANNEL:diffuse;$UDIM:1001;
    Returns list of imageIDs of all imported files, error list, """
    
    lx.eval('select.drop item') # clear selection
    
    data = [] # store imported image maps
    clipList = getImageMaps(scanClips())
    error_list = [] # List of images with file name issues
    tag_list = []
    
    for filePath in fileList:
        file_name = get_filename(filePath)
        
        if file_name not in clipList:
            try:
                MARI_vars = parseFileName(fileNameUser, file_name) # extract the MARI filename templates and their values
                if len(MARI_vars['$UDIM']) != 4:
                    raise
                
            except:
                error_list.append(file_name)
                continue
            
            tag = dict2str(MARI_vars) #string for tag entry
            tag_list.append(tag) # save tags
            UVoffSet = getUVoffSet(MARI_vars["$UDIM"]) # UVoff set from UDIM
            
            if UVoffSet != False and MARI_vars:
                UVoffSet = getUVoffSet(MARI_vars["$UDIM"]) # UVoff set from UDIM
                create_imageMap(filePath) # Create image maps in shadertree
                
                # Check the image size and ignore it if it's 8x8 pixels
                sceneservice.select('selection', 'mediaClip')
                clip_name = sceneservice.query('selection')
                if check_clip_size(clip_name) == True and filter_clips == True:
                    lx.eval("clip.delete")
                    lx.eval("texture.delete")
                    break
                else:
                    pass
                  
                # Gamma correction
                if gamma_correction == True:
                    set_gamma(gamma_value)
                
                #Set UV map
                lx.eval("texture.setUV %s" %UVmap_name)
                
                # Set the UV offset values
                sceneservice.select('selection', 'imageMap')
                imap_ID = sceneservice.query('selection')
                data.append(imap_ID) # save image id to list
                
                lx.eval("select.subItem %s set txtrLocator" %locator_ID(imap_ID))
                lx.eval("item.channel txtrLocator$m02 %s" %UVoffSet[0])
                lx.eval("item.channel txtrLocator$m12 %s" %UVoffSet[1])
                
                # Set item tag with all found MARI_vars
                lx.eval("item.tag string CMMT {%s}" %tag)
                lx.eval("texture.parent Render 0")
                sceneservice.select("selection", "imageMap")
            
            else:
                warning_msg("Please select file(s) with an UDIM or change filename template.")
                return False
                break
        
        else:
            lx.out("MARI ToolKit: ", file_name, " clip already in scene.")
            
    return data, error_list
    
def scanMatGroups(mode):
    """Look for UDIM group masks in the shader tree. Returns a list of the ptag values of the group mask.
    mode:
    '$ENTITY'
    '$UDIM'"""
    sceneservice.select("mask.N", "all")
    itemNum = sceneservice.query("mask.N")
    data = []
    
    if mode == '$UDIM':
        for i in range(itemNum):
            sceneservice.select("mask.id", str(i))
            itemTag = sceneservice.queryN("mask.tags")
            if len(itemTag) > 0 and "UDIM" in itemTag[0]:
                # Save the ptag of the material group
                for channel in range(sceneservice.query("channel.N")):
                    sceneservice.select("channel.name", str(channel))
                    if sceneservice.query("channel.name") == "ptag":        
                        data.append(sceneservice.query("channel.value"))
    elif mode == '$ENTITY':
        for i in range(itemNum):
            sceneservice.select("mask.id", str(i))
            itemTag = sceneservice.queryN("mask.tags")
            if len(itemTag) > 0 and "ENTITY" in itemTag[0]:
                # Save the ptag of the material group
                for channel in range(sceneservice.query("channel.N")):
                    sceneservice.select("channel.name", str(channel))
                    if sceneservice.query("channel.name") == "ptag":        
                        data.append(sceneservice.query("channel.value"))
        
    return data

def renderID():
    """Return the render ID of the scene"""
    sceneservice.select("render.N", "all")
    itemNum = sceneservice.query("render.N")
    for i in range(itemNum):
        sceneservice.select("render.id", str(i))
        return sceneservice.query("item.id")
        break

#def UDIMSets2(meshIDs):
    #"""Return a list of UDIM selection sets. A list of meshIDs must be given"""
    
    #lx.eval('select.drop item mesh') # Clear selection
    #data = []
    ## Select all meshes
    #for mesh in meshIDs:
        #lx.eval('select.subItem %s add mesh' %mesh)
    
    ## Compare name of polyset and store the UDIM sets in a list
    #polysetNum = layerservice.query("polset.N")
    #for i in range(polysetNum):
        #layerservice.select("polset.name", str(i))
        #polySetName = layerservice.query("polset.name")
        #if "UDIM" in polySetName and polySetName not in data:
            #data.append(polySetName)
            
    #lx.eval('select.drop item mesh')
    
    #return data

def UDIMSets(meshIDs):
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

def createMask(maskColorTag, itemList, mode, createMat=True):
    """
    Create material groups for each UDIM. If createMat True each group has its own material.
    The group is assigned via the UDIM selection sets.
    mode: itemMask, groupMask
    """
    if mode == 'groupMask':
        for item in itemList:
            if item not in scanMatGroups('$UDIM'):
                # Create group mask with tags
                lx.eval("shader.create mask")
                lx.eval("texture.parent %s 0" %renderID())
                lx.eval("item.tag string CMMT {%s}" %item)
                lx.eval("item.editorColor %s" %maskColorTag)
                lx.eval("mask.setPTagType {Selection Set}")
                lx.eval("mask.setPTag {%s}" %item)
                
                if createMat == True:
                    # create material in created group
                    lx.eval("shader.create advancedMaterial")
                    lx.eval('item.tag string CMMT {%s}' %item)
            
            else:
                lx.out("MARI ToolKit: ", item, " existing.")
    elif mode == 'itemMask':
        for item in itemList:
            if item not in scanMatGroups('$ENTITY'):
                # Create item mask with tags
                lx.eval("shader.create mask")
                lx.eval("texture.parent %s 0" %renderID())
                lx.eval("item.tag string CMMT {%s}" %item)
                lx.eval("item.editorColor %s" %maskColorTag)
                # extract mesh name:
                #lx.eval('mask.setMesh {0}'.format(item))
                
def moveImageMaps(imageTags, maskTags):    
    '''Move image maps which are in the root and have a $UDIM tag into their masks in the shader tree.
    Expects two lists from getItemTags()'''
    for imageID in imageTags[0]:
        index = imageTags[0].index(imageID) # index in the list to get the coresponding tag
        imageTag = imageTags[1][index] # the tag of the image
        lx.out(imageTag)

        # Parent check
        # If image is in the root ('Render') find the corresponding mask group
        # and move it under it.
        sceneservice.select('item.id', imageID)
        sceneservice.select('item', sceneservice.query('item.parent'))
        if sceneservice.query('item.type') == 'polyRender':
            for maskTag in maskTags[1]:
                lx.out('maskTag:', maskTag)
                try:
                    if maskTag['$UDIM'] == imageTag['$UDIM']:
                        # Retrieve the maskID with index of masks list form masks[0]
                        mask_index = maskTags[1].index(maskTag)
                        maskID = maskTags[0][mask_index]
                        lx.eval('select.item {0} set'.format(imageID))
                        lx.eval('texture.parent {0} 1'.format(maskID))
                except:
                    pass

### DEPRICATED ###                
#def sortIntoGroups():
    #"""Move imported textures into UDIM groups. Only textures which are directly underneath the render node and have a UDIM tag are sorted.
    #If a UDIM group does not excist the texture is not moved."""
    #sceneservice.select("item.N", "all")
    #itemNum = sceneservice.query("item.N")
    #imageDict = {}
    #maskDict = {}
    #for i in range(itemNum):
        #sceneservice.select("item.type", str(i))
        #itemType = sceneservice.query("item.type")
        #itemTag = sceneservice.queryN("item.tags") # first of query is always the comment tag of a item
        #try:
            #itemTag = tagStr2Dict(itemTag[0])
            #UDIM = itemTag["$UDIM"]

            #if  itemType == "imageMap" and "$UDIM" in itemTag and sceneservice.query("item.parent") == renderID():
                #sceneservice.select("item.id", str(i)) # Set the selection back to the current image item
                #imageID = sceneservice.query("item.id")
                
                #try:
                    #imageDict[UDIM].append(imageID)
                #except:
                    #imageDict[UDIM] = [imageID]
                
            #elif itemType == "mask" and "$UDIM" in itemTag:
                #maskID = sceneservice.query("item.id")
                #maskDict[UDIM] = maskID
        #except:
                #pass
### DEPRICATED ### 
    
    for key in imageDict:
        if key in maskDict:
            for i in imageDict[key]:
                lx.eval("select.subItem %s set textureLayer" %i)
                lx.eval("texture.parent %s -1" %maskDict[key])
                lx.out("MARI ToolKit: %s moved to %s"%(i, maskDict[key]))

def checkSelSets(meshIDs):
    """Check if selection sets are already created for the selected mesh item."""
    if not UDIMSets(meshIDs):
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
        itemList = selection
        
    elif imageItemList is None and not selection:
        itemList = []
        sceneservice.select("imageMap.N", "all")
        for i in range(sceneservice.query("imageMap.N")):
            sceneservice.select("imageMap.id", str(i))
            itemList.append(sceneservice.query("item.id"))
    
    elif imageItemList is not None:
        itemList = imageItemList
    
    for item in itemList:
        try:
            sceneservice.select("item.type", str(item))
            itemTag = sceneservice.queryN("item.tags")
            itemTag = tagStr2Dict(itemTag[0])
            for tag, tagValue in itemTag.iteritems():
                if tagValue in chan_values:
                    lx.eval("select.subItem {%s} set textureLayer" %item)
                    lx.eval("shader.setEffect {%s}" %chan_values[tagValue])
                    lx.out("MARI ToolKit: Changed Shader Effect for ", item)
                else:
                    pass
        except:
            lx.out("MARI ToolKit: No valid item tag found")
            
            
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


def getMeshItems():
    '''Return dict with mesh item names and IDs: Key: mesh.name, value: mesh.id
    And mode= None, "all", "selection"
    Example: ({'Mesh':'mesh023'},"all")'''
    sceneservice.select('selection', 'mesh')
    mesh_sel = sceneservice.queryN('selection')
    mesh_dict = {}
    mode = None
    
    if mesh_sel:
        mode = 'selection'
        for mesh_id in mesh_sel:
            sceneservice.select('mesh.id', str(mesh_id))
            mesh_name = sceneservice.query('mesh.name')
            mesh_dict[mesh_name] = mesh_id
        
        return mesh_dict, mode
    
    # If nothing is selected go through all mesh layer if user excepts
    elif not mesh_sel and dialog_yesNo('No Mesh Selected', 'Should I go through all mesh layer which names match the texture name?'):
        sceneservice.select('mesh.N', 'all')
        mesh_num = sceneservice.query('mesh.N')
        mode = 'all'
        for num in range(mesh_num):
            sceneservice.select('mesh.id', str(num))
            mesh_id = sceneservice.query('mesh.id')
            mesh_name = sceneservice.query('mesh.name')
            mesh_dict[mesh_name] = mesh_id
        
        return mesh_dict, mode
    
    else:
        lx.out('I did nothing.')
        return mode

        
def shaderTreeIndex(parent, item):
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
        
        # Check the item type and find the items position in shader tree
        # Dict structure: {parent:[[indices],[items]]}
        data = {}
        for item in itemList:
            sceneservice.select('item', item)
            if sceneservice.query('item.type') == item_type:
                parent = sceneservice.query('item.parent')
                try:
                    data[parent][0].append(shaderTreeIndex(parent, item))
                    data[parent][1].append(item)
                except:
                    data[parent] = [[shaderTreeIndex(parent, item)],[item]]
        
        # Sort the items in the shader tree
        for parent, value in data.iteritems():
            bottomItem = (min(value[0]))
            itemList = value[1]
            for item in itemList:
                lx.eval('select.item {0} set'.format(item))
                lx.eval('texture.parent {0} {1}'.format(parent, bottomItem))
    else:
        lx.out('Nothing selected. Or wrong type defined')

    
def getItemTags(item_type='all'):
    '''Find item tags in scene created from the MARI Tool Kit. Default: all items are searched.
    Returns two lists list[0]==[items];list[1]=={tags}.'''
    sceneservice.select('item.N', 'all')
    item_num = sceneservice.query('item.N')
    items = []
    tags = []
    for item in xrange(item_num):
        sceneservice.select('item', str(item))
        if sceneservice.query('item.type') == item_type:
            try:
                itemTag = sceneservice.queryN('item.tags')[0]
                # If a '$' is found it is most likely an item form the MARI Tool Kit
                if '$' in itemTag:
                    items.append(sceneservice.query('item.id'))
                    tags.append(tagStr2Dict(itemTag))
            except:
                pass
    if len(items) == len(tags):
        return items, tags
    else:
        lx.out('Error - getItemTags(): lists dont match.')

## string conversions ##
def dict2str(dictionary):
    """Convert a dictionary to a string.
    returns 'key2:value2;key2:value2'"""
    string = ""
    for key,value in dictionary.iteritems():
        string += key + ":" + value + ";"
    return string

def tagStr2Dict(tagStr):
    """Convert a tag from a comment to a dictionary.
    Keys in string must be delimited by ';'
    Values must be delimited by ':'
    e.g.: '$UDIM:1002;$CHANNEL:DIFFUSE;'"""
    
    tagStr = filter(None, tagStr.split(";"))
    data={}
    for i in tagStr:
        i=i.split(":")
        data[i[0]]=i[1]
    
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

def dialog_yesNoCancel(header, text):
    try:
        lx.eval("dialog.setup yesNoCancel")
        lx.eval("dialog.title {%s}" %header)
        lx.eval("dialog.msg {%s}" %text)
        lx.eval("dialog.result ok")
        lx.eval("dialog.open")
        return lx.eval("dialog.result ?")
    
    except RuntimeError:
        return lx.eval("dialog.result ?")


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

##---------------------------------------------##
###---------------METHODS END --------------------------###


## MODO SERVICES ##
layerservice = lx.Service("layerservice")
sceneservice = lx.Service("sceneservice")

## VARIABLES ##
args = lx.args()[0] # Arguments. Only the first argument is passed.

layerservice.select('layer.id','main')
layer_index = layerservice.query('layer.index') #select the current mesh layer

layerservice.select('vmap.N', 'all')
vmap_num = layerservice.query('vmap.N') # Number of vertex maps of selected mesh
maskColorTag = "none" # Color tag for UDIM mask groups


#################################
#           USER VALUES         #
#################################
gamma_correction = lx.eval("user.value MARI_TOOLS_gamma ?") # Gamma correction on/off
gamma_value = lx.eval("user.value MARI_TOOLS_gammavalue ?") # Gamma value from UI
fileNameUser =  lx.eval("user.value MARI_TOOLS_filename ?") # Filename structure
filter_clips = lx.eval("user.value MARI_TOOLS_filter_clips ?") # Delete 8x8 clips on/off
create_maskGroups = lx.eval("user.value MARI_TOOLS_create_maskGroups ?") # create missing UDIM mask groups on/off


######################################
#            ARGUMENTS               #
######################################

#####################
#       IMPORT      #
#####################

# Import & organize textures into groups #
if args == "organizeLoadFiles":
    sceneservice.select('selection', 'mesh')
    mesh_items = sceneservice.queryN('selection')
    entity_status = '$ENTITY' in fileNameUser
    
    # Check the selection if nothing is selected all mesh items are stored in a dict if $ENTITY is specified.
    try:
        mesh_items[0]
        selection_status = True
    except:
        selection_status = False
        mesh_items = {}
        if entity_status == True:
            sceneservice.select('mesh.N', 'all')
            for i in range(sceneservice.query('mesh.N')):
                sceneservice.select('mesh.id', str(i))
                mesh_items[sceneservice.query('mesh.name')] = sceneservice.query('mesh.id')
            
    if "$UDIM" not in fileNameUser:
        warning_msg("UDIM is missing in the filename template.")
    
    # Check if a UV set is selected
    elif vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
        
    elif selection_status == False and entity_status == False:
        warning_msg("Please Select an appropriate mesh layer.")
    
    else:
        UVmap_name = vmap_selected(vmap_num, layer_index)        
        fileList = load_files() # Open dialog to load image files
        
        # Import images and get list of imported itemIDs
        imageItemList = createTextures(UVmap_name, fileList, gamma_correction, gamma_value)
        
        if fileList and selection_status == True and imageItemList[0] != False:
            checkSelSets(mesh_items) # Check if selection sets are excisting for all mesh items
            
            # create the material groups with color tag and comment tag
            for mesh, UDIMs in UDIMSets(mesh_items).iteritems():
                createMask(maskColorTag, UDIMs, 'groupMask')
                #lx.eval('select.item drop')
            
            #sortIntoGroups()
            
            moveImageMaps(getItemTags('imageMap'), getItemTags('mask'))
            
            # Set the Shader effect of the imported textures
            setShaderEffect(imageItemList[0])
            
            #Error logging
            lx.out('MARIToolKit: FILENAME ERROR:\n %s' %('\n'.join(imageItemList[1])))
        
        # If nothing is selected all meshes which match the $ENTITY are used.    
        elif fileList and selection_status == False and imageItemList != False:
            meshes_found = []
            for image in imageItemList[0]:
                sceneservice.select('imageMap.tags', str(image))
                try:
                    meshes_found.append(mesh_items[tagStr2Dict(sceneservice.query('imageMap.tags'))['$ENTITY']])
                except:
                    pass
            
            checkSelSets(meshes_found)
            
            for mesh, UDIMs in UDIMSets(meshes_found).iteritems():
                createMask(maskColorTag, UDIMSets(meshes_found), 'groupMask') # create the material groups with color tag and comment tag

            #sortIntoGroups() 
            
            moveImageMaps(getItemTags('imageMaps'), getItemTags('mask'))

            # Set the Shader effect of the imported textures
            setShaderEffect(imageItemList[0]) 
            
            #Error logging
            lx.out('MARIToolKit: FILENAME ERROR:\n %s' %('\n'.join(imageItemList[1])))
            
        else:
            lx.out("MARI ToolKit: Import Error")
    
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
            createTextures(UVmap_name, fileList, gamma_correction, gamma_value)[0]
        else:
            lx.out("MARI ToolKit: Canceld by user.")


#####################
#       TOOLS       #
#####################

# Sort into material groups
elif args == "sortToGroups":
    if create_maskGroups == True:
        sceneservice.select('mesh.N','all')
        
        mesh_items = []
        for i in range(sceneservice.query('mesh.N')):
            sceneservice.select('mesh.id',str(i))
            mesh_items.append(sceneservice.query('mesh.id'))
        for mesh, UDIMs in UDIMSets(mesh_items).iteritems():    
            createMask(maskColorTag, UDIMs, 'groupMask')
        moveImageMaps(getItemTags('imageMaps'), getItemTags('mask'))
        
    else:
        moveImageMaps(getItemTags('imageMaps'), getItemTags('mask'))

# Gamma Correction: Correct Gamma of textures 1.0/2.2 = 0.4546 #
elif args == "gammaCorrect":
    set_gamma(gamma_value)


# set the UVoffset according to $UDIM in comment tag #
elif args == "setUVoffset":
    sceneservice.select('selection', 'imageMap')
    imap_selection = sceneservice.queryN('selection')
    for imap in imap_selection:
        sceneservice.select("item.type", str(imap))
        itemTag = sceneservice.queryN("item.tags") # first of query is always the comment tag of a item
        txtrLoc = lx.eval("texture.setLocator {%s} ?" %imap)
        try:
            itemTag = tagStr2Dict(itemTag[0])
            UDIM = itemTag["$UDIM"]
            lx.eval("select.subItem {%s} set" %txtrLoc)
            lx.eval("item.channel txtrLocator$m02 %s" %getUVoffSet(UDIM)[0])
            lx.eval("item.channel txtrLocator$m12 %s" %getUVoffSet(UDIM)[1])                
            lx.eval("item.channel txtrLocator$tileU reset")
            lx.eval("item.channel txtrLocator$tileV reset")
    
        except:
            continue


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
        lx.eval("@UV_tools.py create_selSets")

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

elif args == "testing":
    lx.out("-----TESTING-----")
    #sceneservice.select('selection', 'mesh')
    #meshIDs = sceneservice.queryN('selection')
    
    filename = 'Mesh01.DIFFUSE.1002'
    
    imageTags = getItemTags('imageMap')
    maskTags = getItemTags('mask')
    
    moveImageMaps(imageTags, maskTags)
    



else:
    lx.out("MARI ToolKit: ")
    lx.out("Please choose one argument: loadFiles, gammaCorrect, setUVoffset, sortSelection, createPolySets, fixUVs")    