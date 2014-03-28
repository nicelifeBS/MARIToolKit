#python

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
            lx.eval("mask.setPTag %s" %selSetName)
            
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
        itemTags = sceneservice.queryN("item.tags")
        try:
            UDIM = itemTags[0]
            if  itemType == "imageMap" and "UDIM" in itemTags[0] and sceneservice.query("item.parent") == renderID():
                sceneservice.select("item.id", str(i)) # Set the selection back to the current image item
                imageID = sceneservice.query("item.id")
                imageDict[UDIM] = imageID
                
            elif itemType == "mask" and "UDIM" in itemTags[0]:
                maskID = sceneservice.query("item.id")
                maskDict[UDIM] = maskID
        except:
                continue
    
    for key in imageDict:
        if key in maskDict:
            lx.eval("select.subItem %s set textureLayer" %imageDict[key])
            lx.eval("texture.parent %s -1" %maskDict[key])

def checkSelSets():
    if not UDIMSets():
        lx.eval("@UV_tools.py create_selSets")
    else:
        pass

# MODO services
sceneservice = lx.Service("sceneservice")
layerservice = lx.Service("layerservice")

# Variables
maskColorTag = "orange"



#checkSelSets()
#lx.out("matgroups: ", scanMatGroups())
createMaterial(maskColorTag)
sortIntoGroups()


