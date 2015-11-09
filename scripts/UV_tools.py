#python

"""
UV_tools v1.4
Author: Bjoern Siegert aka nicelife

Last edit: 2014-01-21

UV_tools.py createselSets|fix_uvs

create_selSets
Creates poly selection sets based on the UV offset values. Each sector containing polys will get a selection set.
The name follows the UDIM scheme of MARI. E.g.: If u and v are between 0-1 the space 0-1 gets a selection set with the name $UDIM:1001,
1-2: $UDIM:1002. If v = 1-2 -> $UDIM:1011, $UDIM:1012,...

fix_uvs
-Moves uv points slightly which lie directly on a U or V border (e.g. 0 or 1) so they fit in one UDIM.
-Selects polys which are in two or more UDIMs

Problems:
- Slow with big models
"""

import time

def repack_selected():
    '''repacks selected uvs in their udim'''

    lx.eval('tool.set util.udim on')
    lx.eval('udim.fit')
    udim = lx.eval('tool.attr util.udim number ?')
    lx.eval('uv.pack true true true auto 0.2 false false udim %s' % udim)
    lx.eval('tool.set util.udim off')    


def selected_uvmap():
    """
    Return the index of the current selected uv map
    """
    # Get the name of selected uv map
    selected_uv_map = lx.eval("vertMap.list type:txuv ?")
    
    # Get the index of the selected uv map
    if selected_uv_map != "_____n_o_n_e_____":
        # Select the vmap and store all the vmap names
        layer.select("vmaps", "all")
        vmap_list = layer.query("vmap.name")
        
        for vmap in xrange(len(vmap_list)):
            layer.select("vmap.index", str(vmap))
            
            # Compare vmap name with the selected uv map. If it matches we have the index we need.
            if layer.query("vmap.name") == selected_uv_map:
                vmap_index = vmap
                return vmap_index
            
    else:
        lx.out("Hey mate, you didn't select a proper UV map. So all I did was printing this stupid message.")
        # Warning dialog!


def check_selSets():
    """
    Check if there are already some UDIM selection set in the scene.
    If yes these will be deleted to give it a fresh start
    """
    
    lx.eval("select.type polygon") # Type polygon because we want to look up poly selection sets
    layer.select("polsets")
    num_polySet = layer.query("polsets")

    if num_polySet:
        
        # List to store the sets to delete
        delete_sets = []
        
        for i in num_polySet:
            # Select the poly set
            layer.select("polset.index", str(i))
            poly_set_name = layer.query("polset.name")
            
            # Find a UDIM selection set and delete it
            if "$UDIM:" in poly_set_name:
                delete_sets.append(poly_set_name)
                
            else:
                pass
        
        # Delete Sets
        layer.select("layer.index", str(layer_index))
        lx.out(layer.query('layer.name'))
        for sets in delete_sets:
            lx.eval("select.deleteSet {%s}" %sets)
            lx.out("Deleted Selection Set: ", sets)


def uv_list(poly_list):
    """
    Here we fill the uv_dict with the poly indices
    We only need the first uv values of the polygon. This is 
    enough to identify uv sector.
    
    Returns a dictionary. The key is the UDIM, the value is a nested list starting with
    the poly index followed by its uv values
    {UDIM:[poly_index,[(u,v),(u,v)]]}
    """
    # Select the current uv map
    layer.select("vmap.index", str(selected_uvmap()))
    
    uv_dict = {} # dict to store our results
    
    for poly in poly_list:
        layer.select("poly.index", str(poly))
        vmap_value = layer.query("poly.vmapValue")
        
        # For the UDIM we need to get the first u and v value.
        # All other uvs of the poly must lie in the same uv space
        # so we don't bother with the remaining ones.
        # Since we are only interessted in full numbers we convert
        # u and v to integer. int() always rounds down! E.g. '0.99' -> '0'
        u = int(vmap_value[0])
        v = int(vmap_value[1])
        
        # Here we fill the final dict with the UDIM key and poly index values
        # If the key is not found in the dict it is created via the exception
        # The result: # {UDIM:[poly_id,...]}
        try:
            uv_dict[1001 + (v * 10) + u ].append(poly)
            
        except KeyError:
            uv_dict[1001 + (v * 10) + u ] = [poly]  
        
    return uv_dict


def tuple_group(old_list):
    """
    Group a list into tuple pairs.
    [1,2,3,4,5,6,7,8] -> [(1,2),(3,4),(5,6),(7,8)]
    
    Input: list
    """
    
    new_list = []
    
    for index in xrange(0, len(old_list), 2):
        value = old_list[index:index+2]
        if len(value) == 2:
            new_list.append(tuple(value))
    
    return new_list


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


# LX SERVICE #
layer = lx.Service("layerservice")
progressbar = lx.Monitor()

# ARGS #
args = lx.args()[0] # Arguments. Only the first argument is passed.

# Select layer and get the index
layer.select("layers", "main")
layer_index = layer.query("layer.index")

# Lets start the magic #

##################
# SELECTION SETS #
##################
if args == "create_selSets":
    lx.out("create selection sets for UDIMs")
    
    # timer start
    t1 = time.time()

    # select polygons 
    layer.select("polys", "all")
    poly_list = layer.query("polys")

    check_selSets() # Delete existing selection sets
    uv_dict = uv_list(poly_list) # create the uv_dict    
    
    progressbar.init(len(uv_dict)) # Initialize the progress bar
    
    # Here we select the polys which were stored in the uv_dict
    # and assign them to their UDIM selection set
    #
    # iteritems() is faster and gives access to key and
    # value at the same time.
    for UDIM,value in uv_dict.iteritems():
        
        # Clear selection
        lx.eval("select.drop polygon")
        
        # Select poly form the uv_dict.
        for poly_index in value:
            lx.eval("select.element %s polygon add %s" %(layer_index, poly_index))
            
        # Create a new selection set with the UDIM as name: $UDIM:1011
        lx.eval("select.editSet {$UDIM:%s} add" %UDIM)
        
        # Logging
        lx.out("New selection set created: $UDIM:",UDIM)
        
        # Clear selection
        lx.eval("select.drop polygon")
        
        # Progressbar step
        progressbar.step(1)
        
    # timer stop
    t2 = time.time()
    sets_creation = t2 - t1
    lx.out("Selection Sets Creation: %s sec" %sets_creation)
    

# FIX UVs #
elif args == "fix_uvs":

    #Check if all polys are in a UDIM sector.
    #If a poly is overlapping select it and give warning!
    
    # Logging
    lx.out("fixing uvs so all points are in one UDIM")
    
    # Selecting
    layer.select("polys", "all")
    poly_list = layer.query("polys")
    layer.select("vmap.index", str(selected_uvmap()))
    
    # Variables
    bad_polys = []
    trans_value = 0.0001 # translation value for the uv points
    
    progressbar.init(len(poly_list)) # Initialize the progress bar
    
    # Lets fix some UVs
    for poly_index in poly_list:
        layer.select("poly.index", str(poly_index))
        uv_pos = tuple_group(layer.query("poly.vmapValue"))
        vert_list = layer.query("poly.vertList")
        
        lx.eval("select.type vertex")
        
        # View type to UV editor
        lx.eval("tool.viewType uv")
        
        for uv in uv_pos:
            
            if uv[0] == round(uv[0]):
                
                # Check if u on the left or right side
                if uv[0] != 0 and uv[0] / round(uv[0]) == 1:
                    trans_value = -abs(trans_value)
                else:
                    trans_value = abs(trans_value) # always positiv
                    
                lx.out("move vert %s poly %s" %(vert_list[uv_pos.index(uv)], poly_index))
                lx.eval("select.element %s vertex set %s 0 %s" %(layer_index, vert_list[uv_pos.index(uv)], poly_index))
                lx.eval("tool.set TransformMove on")
                lx.eval("tool.reset xfrm.transform")
                lx.eval("tool.setAttr xfrm.transform U %s" %(trans_value))
                lx.eval("tool.doApply")
                lx.eval("tool.set TransformMove off")
                
            elif uv[1] == round(uv[1]):
                
                # Check if v on the left or right side
                if uv[1] != 0 and uv[1] / round(uv[1]) == 1:
                    trans_value = -abs(trans_value)
                else:
                    trans_value = abs(trans_value)
                
                lx.out("move vert %s poly %s" %(vert_list[uv_pos.index(uv)], poly_index))
                lx.eval("select.element %s vertex set %s 0 %s" %(layer_index, vert_list[uv_pos.index(uv)], poly_index))
                lx.eval("tool.set TransformMove on")
                lx.eval("tool.reset xfrm.transform")
                lx.eval("tool.setAttr xfrm.transform V %s" %(trans_value))
                lx.eval("tool.doApply")
                lx.eval("tool.set TransformMove off")
        
        # Clear selection
        lx.eval("select.drop vertex")
            
        # Here we save all polys which are in two or more UDIMs
        uv_pos = tuple_group(layer.query("poly.vmapValue"))
        for uv in uv_pos:
            if map(int, uv) != map(int, uv_pos[0]) and poly_index not in bad_polys:
                bad_polys.append(poly_index)
                
        # Progressbar step
        progressbar.step(1)
    
    # View type back to 3D view
    lx.eval("tool.viewType xyz")
    
    # Select the bad polygons and prompt a message for the user.
    if bad_polys:
        lx.eval("select.type polygon")
        lx.eval("select.drop polygon")
        for poly_index in bad_polys:
            lx.eval("select.element %s polygon add %s" %(layer_index, poly_index))
        
        # Warning dialog
        warning_msg("I've found some UVs which spread over more than one UDIM.\nPlease have a look. I've selected them for you")