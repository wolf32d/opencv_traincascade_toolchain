import sys
import os
from PIL import Image



in_dir  = sys.argv[1]
out_dir = sys.argv[2]
default_height = int(sys.argv[3])

# get input images 
if os.path.isdir(in_dir):
    pass
elif os.path.isdir("./" + in_dir):
    in_dir = "./" + in_dir
else:
    print term_colors.FAIL + ("ERROR! %s doesn't exist" % in_dir) + term_colors.ENDC
    sys.exit(0)
if in_dir[-1] != "/":
    in_dir += "/"
    
def is_image(file_name):
    for extension in ['.png', '.jpg']:
        if file_name[-4:].lower() == extension:
            return True

# get images file names
img_names = [fn for fn in os.listdir(in_dir) if is_image(fn)]


for img in img_names:
    im = Image.open(os.path.join(in_dir, img))
    
    w, h = im.size

    new_h = default_height
    new_w = int(float(w) * (float(default_height)/float(h)))
    print (new_w, new_h)
    im.resize((new_w, new_h)).save(os.path.join(out_dir, "scaled_"+img))
