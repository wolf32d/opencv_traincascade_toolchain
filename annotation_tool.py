import sys
import os
import pygame
from pygame.locals import * # all keys and everything
from PIL import Image
import numpy as np



class cv_box_image:
    def __init__(self, _img_file_path):
        self.cv_boxes= []
        self.cv_boxes_apect_ratios = []
        self.img_file_path = _img_file_path
        self.pygame_img = pygame.image.load(_img_file_path)

        width, height = self.pygame_img.get_rect()[2:]
        w_scaling_factor = np.ceil(width / 1920.0)
        h_scaling_factor = np.ceil(height / 1080.0)
        self.scaling_factor = int(max(w_scaling_factor, h_scaling_factor))     

       
    def add_box(self, box_data):
        self.cv_boxes.append(box_data)
        new_spect_ratio = float(box_data[2]) / float(box_data[3])
        self.cv_boxes_apect_ratios.append(new_spect_ratio)




def main_loop():        
    # show first image as default
    screen = pygame.display.set_mode( cv_box_images[0].pygame_img.get_rect()[2:] )

    def display_image(cv_box_image, flip=True):
        screen.blit(cv_box_image.pygame_img, cv_box_image.pygame_img.get_rect())
        pygame.display.set_caption("%s, [%i boxes]" % (cv_box_image.img_file_path, len(cv_box_image.cv_boxes)) )
        if cv_box_image.cv_boxes != []:
            for box in cv_box_image.cv_boxes:
                sel_surf = pygame.Surface((box[2], box[3])) # width , height
                
                sel_surf.fill((0, 128, 0))
                pygame.draw.rect(sel_surf, (0, 255, 0), sel_surf.get_rect(), 1)
                sel_surf.set_alpha(100)
                
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
            """        
            if event.type == pygame.KEYDOWN and event.key == K_PLUS:
                if cv_box_images[img_index].cv_boxes != []:
                    x, y, width, height = cv_box_images[img_index].cv_boxes[-1]
                    y -= 5
                    x -= 5
                    width += 10
                    height += 10
                    cv_box_images[img_index].cv_boxes[-1] = (x, y, width, height)
                    display_image(cv_box_images[img_index])

            if event.type == pygame.KEYDOWN and event.key == K_MINUS:
                if cv_box_images[img_index].cv_boxes != []:
                    x, y, width, height = cv_box_images[img_index].cv_boxes[-1]
                    y += 5
                    x += 5
                    width -= 10
                    height -= 10
                    cv_box_images[img_index].cv_boxes[-1] = (x, y, width, height)
                    display_image(cv_box_images[img_index])
            """  
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
                
                sel_surf.set_alpha(100)
                top_left_corner = (min(first_selection_corner[0], second_selection_corner[0])), min(first_selection_corner[1], second_selection_corner[1])
                
                
                screen.blit(sel_surf, top_left_corner)
                
                pygame.display.flip()
                

# get images directory path
images_dir_path = sys.argv[1].strip()
if os.path.isdir(images_dir_path):
    pass
elif os.path.isdir("./" + images_dir_path):
    images_dir_path = "./" + images_dir_path
else:
    print "images_dir_path: no such directory"
    sys.exit(0)
    
if images_dir_path[-1] != "/":
    images_dir_path += "/"
    

def is_image(file_name):
    for extension in ['.png', '.jpg']:
        if file_name[-4:].lower() == extension:
            return True
        
# get images file names
img_file_list = [name for name in os.listdir(images_dir_path) if is_image(name)]

# load all images
cv_box_images = []

for img_file_name in img_file_list:
    image_path = os.path.join(images_dir_path, img_file_name)
    cv_box_images.append(cv_box_image(image_path))


# pygame setup screen
pygame.init()
main_loop()
pygame.display.quit()


#generate positive info.dat file
positives_list_name = sys.argv[2]
info_file = open(positives_list_name, "w")

total_boxes_num = 0
for cv_box_image in cv_box_images:

    cv_boxes_num = len(cv_box_image.cv_boxes)
    
    total_boxes_num += cv_boxes_num
    if cv_boxes_num > 0:
        info_line = "%s %i" % (cv_box_image.img_file_path, cv_boxes_num)
        
        for box in cv_box_image.cv_boxes:
            info_line += " %i %i %i %i" % box
        
        info_line += "\n"    
        info_file.write(info_line)
        print info_line.strip()
info_file.close

print
print "Total %i boxes, Done!" % total_boxes_num


all_aspect_ratios = []
for cv_box_image in cv_box_images:
    all_aspect_ratios += cv_box_image.cv_boxes_apect_ratios
    
mean_aspect_ratio = np.mean(np.array(all_aspect_ratios))
print    
print "mean aspect ratio:", mean_aspect_ratio

w = int(24*mean_aspect_ratio)
h = 24

command = "opencv_createsamples -vec out.vec -info %s -bg negatives.dat -num %i -show -h %i -w %i" % (
positives_list_name, total_boxes_num, h, w)

print "opencv_createsamples command:"
print
print command
print







































