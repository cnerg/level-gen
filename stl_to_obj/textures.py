import json

# filenames of all the PBR textures included in game in the textures folder, stored as a dict for each file
TEXTURE_FOLDER = "textures"

NORMAL_OPTIONS = "normal_enabled = true\nnormal_scale = -1.0\n"
DEPTH_OPTIONS = "depth_enabled = true\ndepth_scale = -0.01\ndepth_deep_parallax = false\ndepth_flip_tangent = false\ndepth_flip_binormal = false\n"

class Texture:
    def __init__(self, folder, jpg_dict, uv1_scale = ""):
        self.folder = folder
        self.jpg_dict = jpg_dict
        # uv shouldn't be in the dict because it doesn't need an ext_resource like the .jpgs
        self.uv1_scale = uv1_scale 

# dict of all the textures we already have
texture_dict = dict()
other_textures = dict()

# add textures from a .json file to dict 
# allows contributors to use their own textures (that we don't have)
def load_textures(filename):
    data = ""
    with open(filename, 'r') as f:
        # load JSON object as dictionary
        data = json.load(f)

    textures = data["textures"]
    
    for texture_data in data["textures"]:
        if 'uv_scale1' not in texture_data:
            texture_data['uv_scale1'] = ""
        texture_dict[texture_data['folder']] = Texture(texture_data['folder'],
                                                        texture_data['jpg_dict'],
                                                        texture_data['uv_scale1'])

    # load in textures that don't require .jpgs
    if "other_textures" in data:
        for key in data["other_textures"]:
            other_textures[key] = data["other_textures"][key]

# debug printout to check if we load our provided textures correctly
if __name__ == "__main__":
    load_textures("textures.json")
    for i in texture_dict:
        print(i)
    for i in other_textures:
        print(i)