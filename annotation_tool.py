import sys
import os
import pygame
from pygame.locals import * # all keys and everything
from PIL import Image
import numpy as np
from optparse import OptionParser


class term_colors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class cv_box_image:
    def __init__(self, _img_file_path):
        self.cv_boxes= []
        self.cv_boxes_apect_ratios = []
        self.img_file_path = _img_file_path
        # load the image file as pygame image
        full_pygame_img = pygame.image.load(_img_file_path)
        
        # evaluate scaling factor
        full_size = full_pygame_img.get_rect()[2:]
        width, height = full_size 
        w_scaling_factor = np.ceil(width / 1920.0)
        h_scaling_factor = np.ceil(height / 1080.0)
        self.scaling_factor = int(max(w_scaling_factor, h_scaling_factor))           
        
        # scaled version of the image
        scaled_size = tuple([e / self.scaling_factor for e in full_size])
        self.pygame_img = pygame.transform.scale(full_pygame_img, scaled_size)

       
    def add_box(self, box_data):
        self.cv_boxes.append(box_data)
        new_spect_ratio = float(box_data[2]) / float(box_data[3])
        self.cv_boxes_apect_ratios.append(new_spect_ratio)




def main_loop():        
    # show first image as default
    screen = pygame.display.set_mode( cv_box_images[0].pygame_img.get_rect()[2:] )

    def display_image(cv_box_image, flip=True):
        screen.blit(cv_box_image.pygame_img, cv_box_image.pygame_img.get_rect())
            
        window_caption = "%s, [scaled %ix, %i boxes]" % (cv_box_image.img_file_path, cv_box_image.scaling_factor, len(cv_box_image.cv_boxes))
        
        pygame.display.set_caption(window_caption)
        if cv_box_image.cv_boxes != []:
            for box in cv_box_image.cv_boxes:
                sel_surf = pygame.Surface((box[2], box[3])) # width , height
                
                sel_surf.fill((0, 128, 0))
                pygame.draw.rect(sel_surf, (0, 255, 0), sel_surf.get_rect(), 1)
                sel_surf.set_alpha(128)
                
                screen.blit(sel_surf, (box[0], box[1]) ) #top left corner
        if flip:
            pygame.display.flip()
            
    display_image(cv_box_images[0])

    selection_ongoing = False

    old_img_index = 0
    img_index = 0
    old_mouse_pos = (0, 0)

    while True:

        for event in pygame.event.get():
            if event.type == QUIT: 
                return
                
            # go to next image
            if event.type == pygame.KEYDOWN and event.key == K_s:
                if img_index == len(cv_box_images) - 1: # wrap around
                    img_index = 0
                else:
                    img_index += 1
            
            # go to previous image
            if event.type == pygame.KEYDOWN and event.key == K_w:
                if img_index == 0: # wrap around
                    img_index = len(cv_box_images) - 1
                else:
                    img_index -= 1
                    
            if event.type == pygame.KEYDOWN and event.key == K_PLUS:
                if cv_box_images[img_index].cv_boxes != []:
                    x, y, width, height = cv_box_images[img_index].cv_boxes[-1]
                    if y > 4: 
                        y -= 4
                        width += 8
                    if x > 4:
                        x -= 4
                        height += 8

                    cv_box_images[img_index].cv_boxes[-1] = (x, y, width, height)
                    display_image(cv_box_images[img_index])

            if event.type == pygame.KEYDOWN and event.key == K_MINUS:
                if cv_box_images[img_index].cv_boxes != []:
                    x, y, width, height = cv_box_images[img_index].cv_boxes[-1]
                    if width > 8:
                        y += 4
                        width -= 8
                    if height > 8:
                        x += 4
                        height -= 8
                        
                    cv_box_images[img_index].cv_boxes[-1] = (x, y, width, height)
                    display_image(cv_box_images[img_index])
              
            if event.type == pygame.KEYDOWN and event.key == K_BACKSPACE:
                if cv_box_images[img_index].cv_boxes != []:
                    cv_box_images[img_index].cv_boxes.pop()
                    display_image(cv_box_images[img_index]) 
                    

            if event.type == pygame.KEYDOWN and event.key == K_DELETE:
                cv_box_images[img_index].cv_boxes = []
                display_image(cv_box_images[img_index])  
                    
                                        
            if event.type == pygame.MOUSEBUTTONDOWN:
                selection_ongoing = True
                first_selection_corner = pygame.mouse.get_pos()
            
            if event.type == pygame.MOUSEBUTTONUP:
                selection_ongoing = False
                box = (top_left_corner[0], top_left_corner[1], width, height)
                
                # add the new box
                if width != 0 and height != 0:
                    cv_box_images[img_index].add_box(box)
                    display_image(cv_box_images[img_index])
            
            
        # show or refresh current image 
        if (old_img_index != img_index):
            screen = pygame.display.set_mode( cv_box_images[img_index].pygame_img.get_rect()[2:] )
            display_image(cv_box_images[img_index])
            pygame.display.flip()
            old_img_index = img_index
            
        # selection rectangle logic
        if selection_ongoing == True:
            mouse_pos = pygame.mouse.get_pos()
            if (mouse_pos != old_mouse_pos):
                second_selection_corner = mouse_pos
                
                # ongoing selection
                # redraw image before the rectangle BUT DONT'T FLIP    
                display_image(cv_box_images[img_index], flip=False)
                
                # draw selection rectangle on top
                frame = cv_box_images[img_index].pygame_img.get_rect()
                
                width = abs(second_selection_corner[0] - first_selection_corner[0])
                height = abs(second_selection_corner[1] - first_selection_corner[1])
                
                sel_surf = pygame.Surface((width, height))
                sel_surf.fill((0, 0, 128))
                pygame.draw.rect(sel_surf, (0, 0, 255), sel_surf.get_rect(), 1)
                
                sel_surf.set_alpha(128)
                top_left_corner = (min(first_selection_corner[0], second_selection_corner[0])), min(first_selection_corner[1], second_selection_corner[1])
                
                
                screen.blit(sel_surf, top_left_corner)
                
                pygame.display.flip()
                

# get options

usage_str = "usage: %prog [options] data_dir1, data_dir2, ..."

parser = OptionParser(usage=usage_str)

parser.add_option("-p", "--positives-dir", action="store", dest="positives_directory_path",
                  help="positive images directory", metavar="FILE")
parser.add_option("-n", "--name", action="store", dest="cascade_classifier_name",
                  help="cascade classifier name")
(options, opts_args) = parser.parse_args()

positives_directory_path = options.positives_directory_path
cascade_classifier_name  = options.cascade_classifier_name

# get images directory path
if os.path.isdir(positives_directory_path):
    pass
elif os.path.isdir("./" + positives_directory_path):
    positives_directory_path = "./" + positives_directory_path
else:
    print term_colors.FAIL + ("ERROR! %s doesn't exist" % positives_directory_path) + term_colors.ENDC
    sys.exit(0)
    
if positives_directory_path[-1] != "/":
    positives_directory_path += "/"
    

def is_image(file_name):
    for extension in ['.png', '.jpg']:
        if file_name[-4:].lower() == extension:
            return True
        
# get images file names
img_file_list = [name for name in os.listdir(positives_directory_path) if is_image(name)]

if len(img_file_list) == 0:
    print term_colors.FAIL + ("ERROR! no images in %s" % positives_directory_path) + term_colors.ENDC
    sys.exit(0)
    
print "%i image file found" % len(img_file_list)

# load all images
cv_box_images = []

for img_file_name in img_file_list:
    image_path = os.path.join(positives_directory_path, img_file_name)
    cv_box_images.append(cv_box_image(image_path))


# setup the gui
pygame.init()
main_loop()
pygame.display.quit()


#generate positives list file
positives_list_name = cascade_classifier_name + ".dat"
positives_list_file = open(positives_list_name, "w")

total_boxes_num = 0
for cv_box_image in cv_box_images:

    cv_boxes_num = len(cv_box_image.cv_boxes)
    total_boxes_num += cv_boxes_num
    if cv_boxes_num > 0:
        info_line = "%s %i" % (cv_box_image.img_file_path, cv_boxes_num)
        
        for scaled_box_data in cv_box_image.cv_boxes:
            # WRITE DE-SCALED COORDINATES TO FILE
            box_data = tuple([e * cv_box_image.scaling_factor for e in scaled_box_data])
            
            info_line += " %i %i %i %i" % box_data
        
        info_line += "\n"    
        positives_list_file.write(info_line)
        #print info_line.strip()
positives_list_file.close()

print
print "DONE!"
print "Total: %i samples" % total_boxes_num

all_aspect_ratios = []
for cv_box_image in cv_box_images:
    all_aspect_ratios += cv_box_image.cv_boxes_apect_ratios
    
mean_aspect_ratio = np.mean(np.array(all_aspect_ratios))
  
print "mean aspect ratio:", mean_aspect_ratio
width = int(24*mean_aspect_ratio)
height = 24

vec_file_name = cascade_classifier_name + '.vec'

create_samples_command = "opencv_createsamples -vec %s -info %s -num %i -show -h %i -w %i" % (vec_file_name, positives_list_name, total_boxes_num, height, width)

print "starting opencv_createsamples: [press ESC not to show samples]"
print term_colors.OKGREEN + create_samples_command + term_colors.ENDC
print


os.system(create_samples_command)







































