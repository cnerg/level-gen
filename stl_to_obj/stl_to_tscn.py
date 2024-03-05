import aspose.threed as a3d
import argparse
import os
import bpy
import json
import shutil
import textures as Textures # custom module created to store texture info

# example run
# python3.10 stl_to_tscn.py input.txt

# uv map functions from bpy
UV_MAPS = {
    "smart": bpy.ops.uv.smart_project,
    "cube": bpy.ops.uv.cube_project,
    "cylinder": bpy.ops.uv.cylinder_project,
    "sphere": bpy.ops.uv.sphere_project,
    "unwrap": bpy.ops.uv.unwrap
}

# generates an .obj file with uv maps from an .stl file
def generate_obj_file(stl_file, output_prefix, uv_map_type, limited_dissolve = True):
    # reset bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # import .stl into bpy
    bpy.ops.import_mesh.stl(filepath = stl_file)

    # Get all objects in selection
    selection = bpy.context.selected_objects

    # Get the active object
    active_object = bpy.context.active_object

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    for obj in selection:
        # Select each object
        obj.select_set(True)
        # Make it active
        bpy.context.view_layer.objects.active = obj
        # Toggle into Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')
        # Select the geometry
        bpy.ops.mesh.select_all(action='SELECT')

        # Use limited dissolve to remove unnecessary faces 
        if limited_dissolve: 
            bpy.ops.mesh.dissolve_limited()
        # Call project operator to generate uv maps
        try:
            UV_MAPS[uv_map_type]()
        except KeyError as e:
            print(f"no uv map generated for {stl_file} due to invalid uv_map_type")

        # Toggle out of Edit Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Deselect the object
        obj.select_set(False)

    # Restore the selection
    for obj in selection:
        obj.select_set(True)

    # Restore the active object
    bpy.context.view_layer.objects.active = active_object

    # Export to obj
    bpy.ops.wm.obj_export(filepath = f"{output_prefix}.obj")

    # remove the .mtl file
    os.remove(f"{output_prefix}.mtl")



def generate_collisons(stl_file, output_prefix):
    # generate fbx file from stl file to create collisions
    fbx_file = f"{output_prefix}.fbx"
    scene = a3d.Scene.from_file(stl_file)
    scene.save(fbx_file)

    # reset bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # import .fbx into bpy
    bpy.ops.import_scene.fbx(filepath = fbx_file)

    # rename all objects as -colonly
    for obj_index, _ in enumerate(bpy.data.objects):
        # every re-name moves the object to the back of the list. 
        bpy.data.objects[0].name = "Volume" + str(obj_index) + "-colonly"

    # export to .gltf
    bpy.ops.export_scene.gltf(filepath = output_prefix + ".gltf")

    # remove the fbx file
    os.remove(fbx_file)

def generate_texture(texture, ext_resource_id, sub_resource_id):
    sub_res_addon = ""
    ext_res_addon = ""

    # check if it's a PBR texture (require .jpgs)
    if texture in Textures.texture_dict:
        sub_res_addon += f'[sub_resource type="SpatialMaterial" id={sub_resource_id}]\n'
        for jpg in Textures.texture_dict[texture].jpg_dict:
            value = Textures.texture_dict[texture].jpg_dict[jpg]
            # form the ext_resource
            ext_res_addon += f'[ext_resource path="res://{Textures.TEXTURE_FOLDER}/{Textures.texture_dict[texture].folder}/{value}" type="Texture" id={ext_resource_id}]\n'
            # add to sub_res_addon
            if jpg in ["albedo", "roughness", "metallic"]:
                sub_res_addon += f"{jpg}_texture = ExtResource( {ext_resource_id} )\n"
            elif jpg == "normal":
                sub_res_addon += Textures.NORMAL_OPTIONS + f"normal_texture = ExtResource( {ext_resource_id} )\n"
            elif jpg == "depth":
                sub_res_addon += Textures.DEPTH_OPTIONS + f"depth_texture = ExtResource( {ext_resource_id} )\n"

            # don't forget to increment ext_resource_id for the next one
            ext_resource_id += 1

        # add uv1_scale if texture has it
        if Textures.texture_dict[texture].uv1_scale:
            sub_res_addon += f"uv1_scale = {Textures.texture_dict[texture].uv1_scale}\n"

    elif texture in Textures.other_textures:
        # only need sub_resource
        sub_res_addon += f'[sub_resource type="SpatialMaterial" id={sub_resource_id}]\n{Textures.other_textures[texture]}'

    return ext_res_addon, ext_resource_id, sub_res_addon 


def main():
    # argparse to take in input.txt
    parser = argparse.ArgumentParser(prog = ".stl to .obj and .tscn file converter")
    parser.add_argument("input_file", type = str, help = "input json filename")
    args = parser.parse_args()

    # read in input .json file
    with open(args.input_file, 'r') as f:
        ######################
        # .tscn file strings #
        ######################
        # all the .obj, .glb, .jpg (textures)
        ext_resource = ""
        ext_resource_id = 1

        # SpatialMaterials (construction of textures)
        sub_resource = ""
        sub_resource_id = 1

        # MeshInstances and collision scenes (.glb)
        nodes = ""


        ###################
        # parse json file #
        ###################
        # load JSON object as dictionary
        data = json.load(f)

        header = data["header"]

        input_folder = header["input_folder"]

        # make the output folder
        output_folder = header["output_folder"]
        try:
            os.mkdir(f"./{output_folder}")
        # delete the folder and remake it if it does exist
        except OSError as error:
            print(f"NOTICE: {output_folder} folder already exists")
            shutil.rmtree(output_folder) # delete folder and contents
            os.mkdir(f"./{output_folder}")

        # load provided textures
        Textures.load_textures("textures.json")
        # (optional) load extra textures 
        if "extra_textures" in header: 
            Textures.load_textures(header["extra_textures"])
        
        # initialize root node
        nodes += f'[node name="{output_folder}" type="Spatial"]\n'

        # (optional) set scale of scene
        if "scale" in header:
            scale = header["scale"]
            nodes += f'transform = Transform( {scale}, 0, 0, 0, {scale}, 0, 0, 0, {scale}, 0, 0, 0 )\n'
        nodes += "\n" # add extra new line to prepare for next node


        ##################################
        # iterate through all .stl files #
        ##################################
        meshes = data["meshes"]

        # keep track of textures so we don't generate them more than once
        texture_index = dict()

        for m in meshes:
            ####################
            # generate texture #
            ####################
            texture = m["texture"]

            # don't generate textures more than once
            if texture not in texture_index:
                ext_res_addon, ext_resource_id, sub_res_addon = generate_texture(texture, ext_resource_id, sub_resource_id)
                ext_resource += ext_res_addon
                sub_resource += f"{sub_res_addon}\n"
                    
                # add the sub resource's index to texture_index so we can use it later 
                texture_index[texture] = sub_resource_id
                sub_resource_id += 1 


            #####################
            # generate obj mesh #
            #####################
            stl_file = m["stl_file"]
            stl_file_extless, _ = os.path.splitext(stl_file)
            stl_file_location = f"{input_folder}/{stl_file}"

            # output filename without a file extension
            output_prefix = output_folder + "/" + stl_file_extless
            
            # Generate .obj file
            if "limited_dissolve" in m:
                generate_obj_file(stl_file_location, output_prefix, m["uv_map"], limited_dissolve=False)
            else:
                generate_obj_file(stl_file_location, output_prefix, m["uv_map"])

            # add it to ext_resource
            ext_resource += f'[ext_resource path="res://models/{output_prefix}.obj" type="ArrayMesh" id={ext_resource_id}]\n'
            # add it to nodes
            nodes += f'[node name="{stl_file_extless}" type="MeshInstance" parent="."]\nmesh = ExtResource( {ext_resource_id} )\nmaterial/0 = SubResource( {texture_index[texture]} )\n\n'

            # move on to next ext_resource
            ext_resource_id = ext_resource_id + 1

            #######################
            # Generate collisions #
            #######################
            if m["collisions"]:
                generate_collisons(stl_file_location, output_prefix)
                # add it to ext_resource
                ext_resource += f'[ext_resource path="res://models/{output_prefix}.glb" type="PackedScene" id={ext_resource_id}]\n'
                            
                nodes += f'[node name="{stl_file_extless}Col" parent="." instance=ExtResource( {ext_resource_id} )]\n\n'

                # move on to next ext_resource
                ext_resource_id = ext_resource_id + 1

        with open(f"{output_folder}/{output_folder}.tscn", 'w') as tscn_file:
            tscn_file.write(f"[gd_scene load_steps={ext_resource_id + sub_resource_id} format=2]\n\n{ext_resource}\n{sub_resource}{nodes}")


if __name__ == "__main__":
    main()