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
    texture_num = lx.eval("query layerservice texture.N ? all")
    # Parse through all textures until texture ID of layer matches the selected one.
    for i in range(texture_num):
        texture_ID = lx.eval("query layerservice texture.id ? %s" %i)
        if texture_ID == imageMap_ID:
            return lx.eval("query layerservice texture.locator ? %s" %i) #retruns the texture locator ID
            break
        else:
            lx.out("no match")

def create_imageMap(clipPath):
    """
    Create material in shader tree. Change it to an image map and set up UV projection type and tiling
    """
    #lx.out("Create Image: texture.N ", lx.eval("query layerservice texture.N ?"))
    
    lx.eval("clip.addStill %s" %clipPath)
    lx.eval("shader.create constant")
    lx.eval("item.setType imageMap textureLayer")
    lx.eval("texture.setIMap {%s}" %get_filename(clipPath))
    lx.eval("item.channel imageMap$aa false")
    lx.eval("item.channel txtrLocator$projType uv")
    lx.eval("item.channel txtrLocator$tileU reset")
    lx.eval("item.channel txtrLocator$tileV reset")
    #layer_index = lx.eval("query layerservice layer.index ? main")
    
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
    """Extract MARI variables from filename (without extension). Returns a dictionary with all found variables and their values"""
    
    # MARI filename variables
    MARI_vars = ["$ENTITY", "$CHANNEL", "$UDIM", "$LAYER", "$FRAME", "$NUMBER", "$COUNT", "$[METADATA VALUE]"]
    
    foundMARI_vars = []
    for i in MARI_vars:
        if i in fileNameUser:
            foundMARI_vars.append(i)
    
    # Search for delimiter in filename
    # All chars which are not within the MARI_vars are seen as delimiter
    # Returns a list of delimiters
    d = fileNameUser
    d = re.split("\\" + "|\\".join(MARI_vars), d)    
    d = filter(None, d) # Clean up list -> remove items which are empty e.g.: ''

    # Extract MARI variables from filename
    fileName = re.split("|\\".join(d), fileName)
    fileName = filter(None, fileName)
    
    fileVars = {}
    for var in foundMARI_vars:
        fileVars[var] = fileName[foundMARI_vars.index(var)]
    lx.out("MARI variables in filename: ", fileVars)
    
    # DEBUG #
    #lx.out("delimiter:" ,d)
    #lx.out(realFileName)
    #lx.out(foundMARI_vars)
    
    return fileVars
    

def get_clipPath(selection):
    """Returns a dictionary. The key is the actual file path of the image map. Per key the current
    position number and the texture ID are saved."""
    list = {}
    for imap in selection:
        for number in range(lx.eval("query layerservice texture.N ?")):
            if lx.eval("query layerservice texture.id ? %s" %number) == imap:
                list [lx.eval("query layerservice texture.clipFile ? %s" %number)] = [number,imap]
    return list


##### DEPRICATED ##########
def get_UDIM(file_name, delimiter):
    """Extract the UDIM value from file name. A file name and a delimiter must be given. Returns False if it is not a MARI texture."""
    for item in file_name.split(delimiter): # try if string is a number and if the length is 4 chars long it is identified as UDIM
        try:
            int(item)
            if len(item) == 4:
                U_offset = -(int(item[3]) - 1)
                V_offset = -(int(item[1:3]))
                return U_offset, V_offset
            
        except ValueError:
            pass
###########################

def getUVoffSet(UDIM):
    """Converts UDIM to UVoff set values. A 4 digit number as UDIM must be given. e.g. 1012"""
    try:
        int(UDIM)
        U_offset = -(int(UDIM[3]) - 1)
        V_offset = -(int(UDIM[1:3]))
        return U_offset, V_offset
        
    except ValueError:
        lx.out("Not a UDIM")
        
    
def check_clip_size(clip_name):
    """Checks the size of a clip and return True if it is 8x8 pixels"""
    
    clip_size = "w:8"
    for i in range(lx.eval("query layerservice clip.N ?")):
        if lx.eval("query layerservice clip.id ? %s" %i) == clip_name:
            clip_info = lx.eval("query layerservice clip.info ? %s" %i)
            clip_info = clip_info.split(" ")
            
            if clip_size in clip_info[1]: 
                lx.out("%s deleted" %clip_name)
                return True
            else:
                lx.out("%s correct size" %clip_name)
                return False

def set_gamma(value):
    """Set gamma with given value for selected images."""
    if not lx.eval("query sceneservice selection ? imageMap"):
        lx.out("nothing selected")
    else:
        lx.eval("item.channel imageMap$gamma %s" %value)

def get_texture_parent(item_ID):
    """Returns the parent of an image map"""
    return lx.eval("query sceneservice textureLayer.parent ? %s" %item_ID)

def vmap_selected(vmap_num, layer_index):
    """See if a UV map of the current layer is selected and returns the name.
    Also returns false if no vmaps are in scene"""
    
    if vmap_num == 0:
        return False
    
    else:
        for i in range(vmap_num):
            vmap_layer = lx.eval("query layerservice vmap.layer ? %s" %i) + 1 # Layer index starts at 1 and not at 0 -> +1 to shift index
            vmap_type = lx.eval("query layerservice vmap.type ? %s" %i) 
    
            if vmap_type == "texture" and vmap_layer == layer_index:         
                if lx.eval("query layerservice vmap.selected ? %s" %i) == True:
                    
                    #lx.out("layer_index: ", layer_index)
                    #lx.out("vmap_layer: ", vmap_layer)
                    #lx.out("vmap_type: ", vmap_type)
                    
                    vmap_name = lx.eval("query layerservice vmap.name ? %s" %i)
                    return vmap_name
                    break
            
            else:
                pass

def createTextures(UVmap_name, fileList, gamma_correction, gamma_value):
    """Import and create the textures in the shader tree.
    All textures have their UDIM assigned as a tag.
    Returns a list of imageIDs of all imported files."""
    
    data = [] # store imported image maps
    
    clipList = getImageMaps(scanClips())
    
    for filePath in fileList:
        lx.eval("select.item %s set" %layer_id) # Select only the Mesh for a fresh start
        file_name = get_filename(filePath)
        
        if file_name not in clipList:
        
            MARI_vars = parseFileName(fileNameUser, file_name) # extract the MARI filename templates and their values
            tag = dict2str(MARI_vars) #string for tag entry
            if "$UDIM" in MARI_vars and len(MARI_vars["$UDIM"]) == 4:
                
                UVoffSet = getUVoffSet(MARI_vars["$UDIM"]) # UVoff set from UDIM
                create_imageMap(filePath) # Create image maps in shadertree
                
                # Check the image size and ignore it if it's 8x8 pixels
                clip_name = lx.eval("query sceneservice selection ? mediaClip")
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
                imap_ID = lx.eval("query sceneservice selection ? imageMap")
                data.append(imap_ID) # save image id to list
                lx.eval("select.subItem %s set txtrLocator" %locator_ID(imap_ID))
                lx.eval("item.channel txtrLocator$m02 %s" %UVoffSet[0])
                lx.eval("item.channel txtrLocator$m12 %s" %UVoffSet[1])
                
                # Set item tag
                lx.eval("item.tag string CMMT {%s}" %tag)
                lx.eval("texture.parent Render 0")
                sceneservice.select("selection", "imageMap")
            else:
                warning_msg("Please select file(s) with an UDIM or change delimiter")
        
        else:
            lx.out(file_name, "clip already in scene.")
            
    return data
    
def scanMatGroups():
    """Look for UDIM group masks in the shader tree. Returns a list of the ptag values of the group mask."""
    sceneservice.select("item.N", "all")
    itemNum = sceneservice.query("item.N")
    data = []
    for i in range(itemNum):
        sceneservice.select("item.type", str(i))
        if sceneservice.query("item.type") == "mask":
            itemTag = sceneservice.queryN("item.tags")
            if len(itemTag) > 0 and  "UDIM" in itemTag[0]:
                
                # Save the ptag of the material group
                for channel in range(sceneservice.query("channel.N")):
                    sceneservice.select("channel.name", str(channel))
                    if sceneservice.query("channel.name") == "ptag":        
                        data.append(sceneservice.query("channel.value"))
                        
    return data

def renderID():
    """Return the render ID of the scene"""
    sceneservice.select("item.N", "all")
    itemNum = sceneservice.query("item.N")
    for i in range(itemNum):
        sceneservice.select("item.type", str(i))
        if sceneservice.query("item.type") == "polyRender":
            return sceneservice.query("item.id")
            break

def UDIMSets():
    # Get UDIM selection sets in scene
    layerservice.select("layer", "main")
    polysetNum = layerservice.query("polset.N")
    data = []
    for i in range(polysetNum):
        layerservice.select("polset.name", str(i))
        polySetName = layerservice.query("polset.name")
        if "UDIM" in polySetName:
            data.append(polySetName)
    return data

def createMaterial(maskColorTag):
    """
    Create material groups for each UDIM. Each group contains a material.
    The group is assigned via the UDIM selection sets.
    """
    for selSetName in UDIMSets():
        if selSetName not in scanMatGroups():
            # Create group mask with tags
            lx.eval("shader.create mask")
            lx.eval("texture.parent %s 0" %renderID())
            lx.eval("item.tag string CMMT {%s}" %selSetName)
            lx.eval("item.editorColor %s" %maskColorTag)
            lx.eval("mask.setPTagType {Selection Set}")
            lx.eval("mask.setPTag {%s}" %selSetName)
            
            maskName = lx.eval("item.name ? mask")
            
            # create material in created group
            lx.eval("shader.create advancedMaterial")
        
        else:
            lx.out(selSetName, " already created.")

def sortIntoGroups():
    """Move imported textures into UDIM groups. Only textures which are directly underneath the render node and have a UDIM tag are sorted.
    If a UDIM group does not excist the texture is not moved."""
    sceneservice.select("item.N", "all")
    itemNum = sceneservice.query("item.N")
    imageDict = {}
    maskDict = {}
    for i in range(itemNum):
        sceneservice.select("item.type", str(i))
        itemType = sceneservice.query("item.type")
        itemTag = sceneservice.queryN("item.tags") # first of query is always the comment tag of a item
        try:
            itemTag = tagStr2Dict(itemTag[0])
            UDIM = itemTag["$UDIM"]
            if  itemType == "imageMap" and "$UDIM" in itemTag and sceneservice.query("item.parent") == renderID():
                sceneservice.select("item.id", str(i)) # Set the selection back to the current image item
                imageID = sceneservice.query("item.id")
                imageDict[UDIM] = imageID
                
            elif itemType == "mask" and "$UDIM" in itemTag:
                maskID = sceneservice.query("item.id")
                maskDict[UDIM] = maskID
        except:
                continue
    
    for key in imageDict:
        if key in maskDict:
            lx.eval("select.subItem %s set textureLayer" %imageDict[key])
            lx.eval("texture.parent %s -1" %maskDict[key])

def checkSelSets():
    """Check if selection sets are already created for the selected mesh item."""
    if not UDIMSets():
        lx.eval("@UV_tools.py create_selSets")
    else:
        lx.out("Selection Sets are there.")
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
        lx.out("Shader effect for selection:")
    elif imageItemList is None and not selection:
        lx.out("Shader effect for all imported:")
        itemList = []
        sceneservice.select("item.N", "all")
        for i in range(sceneservice.query("item.N")):
            sceneservice.select("item.type", str(i))
            if sceneservice.query("item.type") == "imageMap":
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
                    lx.out(item)
                else:
                    pass
        except:
            lx.out("No valid item tag found")
            
            
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

layer_index = lx.eval("query layerservice layer.index ? main") #select the current mesh layer
layer_id = lx.eval("query layerservice layer.id ? main")
scene_index = lx.eval("query sceneservice scene.index ? current")
imap_selection = lx.evalN("query sceneservice selection ? imageMap") # get the name of the selected images
vmap_num = lx.eval("query layerservice vmap.N ?") # Number of vertex maps of selected mesh
maskColorTag = "orange" # Color tag for UDIM mask groups


#################################
#           USER VALUES         #
#################################
gamma_correction = lx.eval("user.value MARI_TOOLS_gamma ?") # Gamma correction on/off
gamma_value = lx.eval("user.value MARI_TOOLS_gammavalue ?") # Gamma value from UI
delimiter =  lx.eval("user.value MARI_TOOLS_delimiter ?") # Delimiter form UI
fileNameUser =  lx.eval("user.value MARI_TOOLS_filename ?") # Filename structure
filter_clips = lx.eval("user.value MARI_TOOLS_filter_clips ?") # Delete 8x8 clips on/off
create_maskGroups = lx.eval("user.value MARI_TOOLS_create_maskGroups ?") # create missing UDIM mask groups on/off

## Delimiter Interpreter ##
if delimiter == "option1":
    delimiter = "."
elif delimiter == "option2":
    delimiter = "_"


######################################
#            ARGUMENTS               #
######################################

#####################
#       IMPORT      #
#####################

# Import & organize textures into groups #
if args == "organizeLoadFiles":
    
    if "$UDIM" not in fileNameUser:
        warning_msg("UDIM is missing in the filename template.")
    
    # Check if a UV set is selected
    elif vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    else:
        UVmap_name = vmap_selected(vmap_num, layer_index)
        fileList = load_files() # Open dialog to load image files
        
        if fileList:    
            # Import images and get list of imported itemIDs
            imageItemList = createTextures(UVmap_name, fileList, gamma_correction, gamma_value)
            
            checkSelSets() # Check if selection sets are created
            createMaterial(maskColorTag) # create the material groups with color tag and comment tag
            sortIntoGroups() 
            
            # Set the Shader effect of the imported textures
            setShaderEffect(imageItemList)
        
        else:
            lx.out("Caneled by user.")
    
# Import only textures strait into the shader tree root #
elif args == "loadFiles":
    
    if "$UDIM" not in fileNameUser:
        warning_msg("UDIM is missing in the filename template.")
    
    # Check if a UV set is selected
    elif vmap_selected(vmap_num, layer_index) == False or not vmap_selected(vmap_num, layer_index):
        warning_msg("Please select a UV map.")
    
    else:
        UVmap_name = vmap_selected(vmap_num, layer_index)
        fileList = load_files() # Open dialog to load image files
        
        if fileList:
            createTextures(UVmap_name, fileList, gamma_correction, gamma_value)
        else:
            lx.out("Canceld by user.")


#####################
#       TOOLS       #
#####################

# Sort into material groups
elif args == "sortToGroups":
    if create_maskGroups == True:    
        createMaterial(maskColorTag)
        sortIntoGroups()
    else:
        sortIntoGroups()

# Gamma Correction: Correct Gamma of textures 1.0/2.2 = 0.4546 #
elif args == "gammaCorrect":
    set_gamma(gamma_value)

# set the UVoffset according to image file name #
elif args == "setUVoffset":
    for imap in imap_selection:
        sceneservice.select("item.type", str(imap))
        itemTag = sceneservice.queryN("item.tags") # first of query is always the comment tag of a item
        txtrLoc = lx.eval("texture.setLocator {%s} ?" %imap)
        try:
            itemTag = tagStr2Dict(itemTag[0])
            UDIM = itemTag["$UDIM"]
            lx.out(txtrLoc)
            lx.eval("select.subItem {%s} set" %txtrLoc)
            lx.eval("item.channel txtrLocator$m02 %s" %getUVoffSet(UDIM)[0])
            lx.eval("item.channel txtrLocator$m12 %s" %getUVoffSet(UDIM)[1])                
            lx.eval("item.channel txtrLocator$tileU reset")
            lx.eval("item.channel txtrLocator$tileV reset")
    
        except:
            continue

# Sort selected images top to bottom #
elif args == "sortSelection":
    clip_list = get_clipPath(imap_selection)
    sorted_list= sorted(clip_list) # Sort keys of dict in alphabetic order
    
    for i in sorted_list:
        lx.out("clip path: ", i)
        
        # If selection is directly parented under Render -> not in a sub group
        if "Render" in get_texture_parent(clip_list[i][1]):
            lx.eval("select.item %s set textureLayer" %clip_list[i][1])
            lx.eval("texture.parent %s 1" %get_texture_parent(clip_list[i][1]))
        
        # If selection is parented in a group
        else:
            lx.eval("select.item %s set textureLayer" %clip_list[i][1])
            lx.eval("texture.parent %s 0" %get_texture_parent(clip_list[i][1]))

# Create poly selection set for each UDIM #
elif args == "createPolySets":
    # Check if a UV map is selected
    lx.out(vmap_selected(vmap_num, layer_index))
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
    lx.out("TESTING")
    
    lx.out(getImageMaps(scanClips()))
    
    
else:
    lx.out("Please choose one argument: loadFiles, gammaCorrect, setUVoffset, sortSelection, createPolySets, fixUVs")    