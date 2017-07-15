import sys
import os
import pygame
import numpy as np
import cv2
from pygame.locals import * # all keys and everything
from PIL import Image
from optparse import OptionParser

class term_colors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'



# mark up box object
class mu_box:
    def __init__(self, _coordinates, _positive_flag):
        # upper left corner x, y, width, heigth
        self.tlx, self.tly, self.width, self.heigth  = list(_coordinates)
        self.positive_flag = _positive_flag # bool type flag
        self.is_cascade_box_flag = False
    def aspect_ratio(self,):
        return float(self.width) / float(self.heigth)
    def color(self,):
        red   = (155, 0, 0)
        green = (0, 128, 0)
        blue  = (0, 0, 200)
        if self.is_cascade_box_flag:
            return blue
        else:
            if self.positive_flag:
                return green
            else:
                return red
            
            
                    
# marked up image object
class cv_mu_image:
    #def __init__(self, _img_file_path, _screen_res=(1080, 1920)): # 90 deg rotation
    def __init__(self, _img_file_path, _screen_res=(1920, 1080)): # default
    
        self.mu_boxes = []
        # load the image file as pygame image
        self.path = _img_file_path
        full_pygame_img = pygame.image.load(_img_file_path)
        
        self.boxes_selective_show = 0 # 0 = ALL
                                      # 1 = pos/neg only
                                      # 2 = haar only   
        # evaluate view inverse scaling factor
        full_size = full_pygame_img.get_rect()[2:]
        width, height = full_size
        w_inv_scaling_factor = np.ceil(height / _screen_res[0])
        h_inv_scaling_factor = np.ceil(height / _screen_res[1])
        self.inv_scaling_factor = int(max(np.ceil(float(width)  / float(_screen_res[0])),
                                          np.ceil(float(height) / float(_screen_res[1])))) / 2
        
        
        # scaled version of the image
        scaled_size = tuple([e / self.inv_scaling_factor for e in full_size])
        self.scaled_pygame_img = pygame.transform.scale(full_pygame_img, scaled_size)
       
    def add_mu_box(self, mu_box):
        self.mu_boxes.append(mu_box)
        
    def show(self, _pygame_screen_obj, _show_pos_flag=True, _show_neg_flag=True):
        screen = _pygame_screen_obj
        # show image itself
        screen.blit(self.scaled_pygame_img, self.scaled_pygame_img.get_rect())
        # show boxes
        for box in self.mu_boxes:
            box_shape = (box.width, box.heigth)
            select_surf = pygame.Surface(box_shape)
            select_surf.fill(box.color())
            pygame.draw.rect(select_surf, (255,255,255) , select_surf.get_rect(), 1)
            
            
            if box.is_cascade_box_flag == True: # cv haar boxes
                if self.boxes_selective_show in [0,2]:
                    select_surf.set_alpha(100)
                else:
                    select_surf.set_alpha(0)
            else: # pos neg boxes
                if self.boxes_selective_show in [0,1]:
                   select_surf.set_alpha(100)
                else:
                    select_surf.set_alpha(0)
                    
            screen.blit(select_surf, (box.tlx, box.tly) ) #top left corner x, y
            # note: do not update_display(pygame.display) here
            # so other functions can draw additional stuff (e.g selection boxes)
        
        
        
# get options

usage_str = ""

parser = OptionParser(usage=usage_str)

parser.add_option("-n", "--name", action="store", dest="cascade_classifier_name",
                  help="cascade classifier name", default="default_cascade_name")
parser.add_option("-i", "--images-folder", action="store", dest="images_folder",
                  help="image folder path")
parser.add_option("-P", "--positive-samples-list", action="store", dest="positive_samples_list",
                  help="positive samples list file", default="default_positive_samples_list.txt")
parser.add_option("-N", "--negative-samples-list", action="store", dest="negative_samples_list",
                  help="negative samples list file", default="default_negative_samples_list.txt")
parser.add_option("-o", "--output-negative-samples-folder", action="store", dest="out_neg_folder",
                  help="output cropped negative samples folder")                  
parser.add_option("-C", "--cascade", action="store", dest="old_cascade_fn",
                  help="load an existing cascade to select further negatives and positives")                 
parser.add_option("-a", "--annotate-only", action="store_true", dest="annotate_only",
                  help="annotate only, do not create postives .vec file and negative samples")
                  
                  
(options, opts_args) = parser.parse_args()


images_folder = options.images_folder
# get images directory path
if os.path.isdir(images_folder):
    pass
elif os.path.isdir("./" + images_folder):
    images_folder = "./" + images_folder
else:
    print term_colors.FAIL + ("ERROR! %s doesn't exist" % images_folder) + term_colors.ENDC
    sys.exit(0)
if images_folder[-1] != "/":
    images_folder += "/"
    
def is_image(file_name):
    for extension in ['.png', '.jpg', '.bmp']:
        if file_name[-4:].lower() == extension:
            return True

# get images file names
new_img_paths = [os.path.join(images_folder, fn) for fn in os.listdir(images_folder) if is_image(fn)]


if len(new_img_paths) == 0:
    print term_colors.FAIL + ("ERROR! no images in %s" % images_folder) + term_colors.ENDC
    sys.exit(0)

# create all cv_mu_images objects
cv_mu_images = []
for img_path in new_img_paths:
    cv_mu_images.append(cv_mu_image(img_path))



negatives_num = 0
positives_num = 0
    
# get old positives files
if os.path.isfile(options.positive_samples_list):
    print "loading %s" % options.positive_samples_list
    old_positives_list = open(options.positive_samples_list, "r").read() #TODO ckeck if exists

    for line in old_positives_list.split('\n'):
        line_data = line.split(' ')
        if len(line_data) > 1:
            old_path = line_data[0]
            boxes_num = int(line_data[1])
            try:
                boxes_data = [int(e) for e in line_data[2:]]
            except(ValueError):
                print term_colors.FAIL + ("ERROR! %s is corrupted" % options.positive_samples_list) + term_colors.ENDC
                sys.exit(0)
                 
            if len(line_data[2:])/4 != boxes_num: # opencv files consistency check
                print term_colors.FAIL + ("ERROR! %s is corrupted" % options.positive_samples_list) + term_colors.ENDC
                sys.exit(0)
            
            old_boxes =[boxes_data[x:x+4] for x in range(0, len(boxes_data),4)]
            
            # if a path is also present in the new image add all the boxes in it
            if old_path in new_img_paths:
                for cv_mu_image in cv_mu_images:
                    if cv_mu_image.path == old_path:
                        for old_box in old_boxes:
                            old_mu_box = mu_box(np.array(old_box)/cv_mu_image.inv_scaling_factor, _positive_flag=True)
                            cv_mu_image.add_mu_box(old_mu_box)
                            positives_num +=1
            else:
                print term_colors.WARNING + ("WARNING: %s is in %s but not in %s folder" % (old_path, options.positive_samples_list, images_folder)) + term_colors.ENDC    
else:
    print "%s does not exist, it will be a new positives file" % options.positive_samples_list


# get cascade boxes from existing cascade
if options.old_cascade_fn != None:
    print "using existing cascade file: %s" % options.old_cascade_fn
    
    
    for cv_mu_image in cv_mu_images:
    
        cascade = cv2.CascadeClassifier(options.old_cascade_fn)    
    
        img = cv2.imread(cv_mu_image.path)
        
        # experimental
        cv_scale_factor = 2.0
        gray_orig = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        gray = cv2.resize(gray_orig, (0,0),
                          fx=cv_scale_factor, fy=cv_scale_factor,
                          interpolation=cv2.cv.CV_INTER_CUBIC)
        
        
    
        detected_objs =  cascade.detectMultiScale(gray,
                                                  minSize=(0, 0),
                                                  flags=cv2.cv.CV_HAAR_SCALE_IMAGE)
        #add a cascade type box
        for (cvx, cvy, cvw, cvh) in detected_objs:
            c_tlx    = int(cvx / (cv_mu_image.inv_scaling_factor * cv_scale_factor))
            c_tly    = int(cvy / (cv_mu_image.inv_scaling_factor * cv_scale_factor))
            c_width  = int(cvw / (cv_mu_image.inv_scaling_factor * cv_scale_factor))
            c_heigth = int(cvh / (cv_mu_image.inv_scaling_factor * cv_scale_factor))
            
            cascade_box_coords = (c_tlx, c_tly, c_width, c_heigth)

            cascade_mu_box = mu_box(cascade_box_coords, _positive_flag=True)
            cascade_mu_box.is_cascade_box_flag = True
            cv_mu_image.add_mu_box(cascade_mu_box)


# get old negatives files
if os.path.isfile(options.negative_samples_list):
    print "loading %s" % options.negative_samples_list
    old_negatives_list = open(options.negative_samples_list, "r").read() #TODO ckeck if exists

    for line in old_negatives_list.split('\n'):
        line_data = line.split(' ')
        if len(line_data) > 1:
            old_path = line_data[0]
            boxes_num = int(line_data[1])
            try:
                boxes_data = [int(e) for e in line_data[2:]]
            except(ValueError):
                print term_colors.FAIL + ("ERROR! %s is corrupted" % options.negative_samples_list) + term_colors.ENDC
                sys.exit(0)
                 
            if len(line_data[2:])/4 != boxes_num: # opencv files consistency check
                print term_colors.FAIL + ("ERROR! %s is corrupted" % options.negative_samples_list) + term_colors.ENDC
                sys.exit(0)
            
            old_boxes =[boxes_data[x:x+4] for x in range(0, len(boxes_data),4)]
            
            # if a path is also present in the new image add all the boxes in it
            if old_path in new_img_paths:
                for cv_mu_image in cv_mu_images:
                    if cv_mu_image.path == old_path:
                        for old_box in old_boxes:
                            old_mu_box = mu_box(np.array(old_box)/cv_mu_image.inv_scaling_factor, _positive_flag=False)
                            cv_mu_image.add_mu_box(old_mu_box)
                            negatives_num += 1
            else:
                print term_colors.WARNING + ("WARNING: %s is in %s but not in %s folder" % (old_path, options.negative_samples_list, images_folder)) + term_colors.ENDC    
else:
    print "%s does not exist, it will be a new negatives file" % options.negative_samples_list
    
    
    

def pygame_loop(init_positives_num, init_negatives_num):

    # setup the pygame gui
    pygame.init()

    # pygame loop logic flags
    global_boxes_selective_show = 0

    positive_sampling_flag = True

    show_pos_boxes = False
    show_neg_boxes = True
    init_flag = True

    ongoing_selection = False

    old_img_index = 0
    img_index = 0
    old_mouse_pos = (0, 0)
    
    positives_num = init_positives_num
    negatives_num = init_negatives_num
    
    current_box_ind = -1
    
    def update_display(pygame_display_obj):
        
        positive_sampling_flag
        ongoing_selection
        img_index
        cv_mu_images
        path = cv_mu_images[img_index].path
        negatives_num
        positives_num 
        
        if positive_sampling_flag:
            pos_neg_str = "POS"
        else:
            pos_neg_str = "NEG"
        
        window_caption = "%s [%s] Np=%i Nn=%i" % (path, pos_neg_str, positives_num, negatives_num)
        pygame_display_obj.set_caption(window_caption)
        pygame_display_obj.flip()

    # pygame events loop
    while True:
        
        # show the new cv_mu_image in the list 
        if (old_img_index != img_index) or init_flag:
            
            cv_mu_images[img_index].boxes_selective_show = global_boxes_selective_show # just a hack, don't need selective view for each image
        
            # also update the screen object
            screen = pygame.display.set_mode( cv_mu_images[img_index].scaled_pygame_img.get_rect()[2:] )
            cv_mu_images[img_index].show(screen)
            update_display(pygame.display)
            old_img_index = img_index
            init_flag = False


        for event in pygame.event.get():
            # quit
            if event.type == QUIT: 
                return
                
            # go to next image
            if event.type == pygame.KEYDOWN and event.key == K_s:
                if img_index == len(cv_mu_images) - 1: # wrap around
                    img_index = 0
                else:
                    img_index += 1
                current_box_ind = -1
            
            # go to previous image
            if event.type == pygame.KEYDOWN and event.key == K_w:
                if img_index == 0:                     # wrap around
                    img_index = len(cv_mu_images) - 1
                else:
                    img_index -= 1
                current_box_ind = -1
                    
            # toggle positive sample mode
            if event.type == pygame.KEYDOWN and event.key == K_p:
                positive_sampling_flag = not positive_sampling_flag
                
                if positive_sampling_flag:
                    print "switched to POSITIVE"
                else:
                    print "switched to NEGATIVE"
                cv_mu_images[img_index].show(screen)
                update_display(pygame.display)
                    
            # change boxes selective view
            if event.type == pygame.KEYDOWN and event.key == K_h:
                if global_boxes_selective_show == 2:
                    global_boxes_selective_show = 0
                else:
                    global_boxes_selective_show += 1
                    
                if global_boxes_selective_show == 0:
                    print "showing ALL BOXES"
                elif global_boxes_selective_show == 1:
                    print "showing POS NEG only"
                else:
                    print "showing HAAR only"
                cv_mu_images[img_index].boxes_selective_show = global_boxes_selective_show
                cv_mu_images[img_index].show(screen)
                update_display(pygame.display)    

            # enlarge current box
            if event.type == pygame.KEYDOWN and event.key == K_PLUS:
                ### TODO
                print "TODO + command"
            
            # shrink current box
            if event.type == pygame.KEYDOWN and event.key == K_MINUS:
                if cv_mu_images[img_index].mu_boxes != []:
                    current_box = cv_mu_images[img_index].mu_boxes[current_box_ind]
                    current_box.width -= 2
                    current_box.tlx += 1
                    current_box.heigth -= 2
                    current_box.tly += 1
                    cv_mu_images[img_index].show(screen)
                    update_display(pygame.display)
                
                
            # notch current box size
            if event.type == pygame.KEYDOWN and event.key == K_RIGHT:
                if cv_mu_images[img_index].mu_boxes != []:
                    current_box = cv_mu_images[img_index].mu_boxes[current_box_ind]
                    current_box.width += 1
                    cv_mu_images[img_index].show(screen)
                    update_display(pygame.display)
                    
            if event.type == pygame.KEYDOWN and event.key == K_LEFT:
                if cv_mu_images[img_index].mu_boxes != []:
                    current_box = cv_mu_images[img_index].mu_boxes[current_box_ind]
                    current_box.width += 1
                    current_box.tlx -= 1
                    cv_mu_images[img_index].show(screen)
                    update_display(pygame.display)
                    
                    
            if event.type == pygame.KEYDOWN and event.key == K_DOWN:
                if cv_mu_images[img_index].mu_boxes != []:
                    current_box = cv_mu_images[img_index].mu_boxes[current_box_ind]
                    current_box.heigth += 1
                    cv_mu_images[img_index].show(screen)
                    update_display(pygame.display)
                    
            if event.type == pygame.KEYDOWN and event.key == K_UP:
                if cv_mu_images[img_index].mu_boxes != []:
                    current_box = cv_mu_images[img_index].mu_boxes[current_box_ind]
                    current_box.heigth += 1
                    current_box.tly -= 1
                    cv_mu_images[img_index].show(screen)
                    update_display(pygame.display)
                    
                                  
            
            # delete current box  
            if event.type == pygame.KEYDOWN and event.key == K_BACKSPACE:
                cv_mu_images[img_index].mu_boxes = [b for i,b in enumerate(cv_mu_images[img_index].mu_boxes) if b.is_cascade_box_flag or i!=current_box_ind]
                cv_mu_images[img_index].show(screen)
                update_display(pygame.display)
                        
                    
            # delete all boxes in current image
            if event.type == pygame.KEYDOWN and event.key == K_DELETE:
                cv_mu_images[img_index].mu_boxes = [b for b in cv_mu_images[img_index].mu_boxes if b.is_cascade_box_flag]
                cv_mu_images[img_index].show(screen)
                update_display(pygame.display) 
                
            # select event: start a new selection
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # 1=LEFT
                ongoing_selection = True
                first_selection_corner = pygame.mouse.get_pos()
                
            # select event: end the selection process and create a new box
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                ongoing_selection = False
                box_coords = (top_left_corner[0], top_left_corner[1], width, height)
                # add the new box to the current image
                if width != 0 and height != 0:
                    cv_mu_images[img_index].add_mu_box(mu_box(box_coords, positive_sampling_flag ))
                    if positive_sampling_flag:
                        positives_num += 1
                    else:
                        negatives_num +=1
                    cv_mu_images[img_index].show(screen)
                    update_display(pygame.display)
                    current_box_ind = -1
                    
                    
                    
            # convert cv box to POS or NEG
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # 3=RIGHT
                for box in cv_mu_images[img_index].mu_boxes:
                    if box.is_cascade_box_flag:
                        
                        click_x, click_y = pygame.mouse.get_pos()
                        if click_x in range(box.tlx, box.tlx+box.width):
                            if click_y in range(box.tly, box.tly+box.heigth): 
                                # convert box
                                box.is_cascade_box_flag = False
                                box.positive_flag = positive_sampling_flag
                                if positive_sampling_flag:
                                    print "CV box converted to POS"                                                  
                                else:
                                    print "CV box converted to NEG"
                                cv_mu_images[img_index].show(screen)
                                update_display(pygame.display)
                                    
            # change current box                        
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # 2=WHEEL DOWN
                for box_ind, box in enumerate(cv_mu_images[img_index].mu_boxes):
                    if not box.is_cascade_box_flag:
                        
                        click_x, click_y = pygame.mouse.get_pos()
                        if click_x in range(box.tlx, box.tlx+box.width):
                            if click_y in range(box.tly, box.tly+box.heigth): 
                                # select box
                                current_box_ind = box_ind
                                print "jumping to box no %i" % box_ind
                
        # selection rectangle logic
        if ongoing_selection == True:
            mouse_pos = pygame.mouse.get_pos()
            if (mouse_pos != old_mouse_pos):
                
                cv_mu_images[img_index].show(screen)

                # draw selection rectangle on top of current image
                second_selection_corner = mouse_pos
                width = abs(second_selection_corner[0] - first_selection_corner[0])
                height = abs(second_selection_corner[1] - first_selection_corner[1])
                
                select_surf = pygame.Surface((width, height))
                select_surf.fill((255, 255, 128))
                pygame.draw.rect(select_surf, (255, 255, 0), select_surf.get_rect(), 1)
                
                select_surf.set_alpha(128)
                top_left_corner = (min(first_selection_corner[0], second_selection_corner[0])), min(first_selection_corner[1], second_selection_corner[1])
                
                screen.blit(select_surf, top_left_corner)           
                update_display(pygame.display)
         
         

pygame_loop(positives_num, negatives_num)         
# quit
pygame.display.quit()


# generate the new positives list file
positives_list_file = open(options.positive_samples_list, "w")

total_positives_num = 0
for cv_mu_image in cv_mu_images:
    positive_mu_boxes = [b for b in cv_mu_image.mu_boxes if b.positive_flag and (not b.is_cascade_box_flag)]
    positive_boxes_num = len(positive_mu_boxes)
    total_positives_num += positive_boxes_num
    if positive_boxes_num > 0:
        list_line = "%s %i" % (cv_mu_image.path, positive_boxes_num)
        
        for pbox in positive_mu_boxes:
            # note: write the non-scaled coordiantes in the positives list file
            descaled_coords = tuple([e * cv_mu_image.inv_scaling_factor for e in (pbox.tlx, pbox.tly, pbox.width, pbox.heigth)])
            
            list_line += " %i %i %i %i" % descaled_coords
        list_line += "\n"    
        positives_list_file.write(list_line)
positives_list_file.close()

print "Done. %i positive sample(s) written to %s" % (total_positives_num, options.positive_samples_list)


# generate the new negatives list file (tool version)
negatives_list_file = open(options.negative_samples_list, "w")

total_negatives_num = 0
for cv_mu_image in cv_mu_images:
    negative_mu_boxes = [b for b in cv_mu_image.mu_boxes if (not b.positive_flag) and (not b.is_cascade_box_flag)]
    negative_boxes_num = len(negative_mu_boxes)
    total_negatives_num += negative_boxes_num
    if negative_boxes_num > 0:
        list_line = "%s %i" % (cv_mu_image.path, negative_boxes_num)
        
        for pbox in negative_mu_boxes:
            # note: write the non-scaled coordiantes in the negatives list file
            descaled_coords = tuple([e * cv_mu_image.inv_scaling_factor for e in (pbox.tlx, pbox.tly, pbox.width, pbox.heigth)])
            
            list_line += " %i %i %i %i" % descaled_coords
        list_line += "\n"    
        negatives_list_file.write(list_line)
negatives_list_file.close()

print "Done. %i negative sample(s) written to %s" % (total_negatives_num, options.negative_samples_list)

 
if not options.annotate_only:
    # generate cropped negatives and the new negatives list file (opencv version)
    if not os.path.isdir(options.out_neg_folder):
        print term_colors.FAIL + ("ERROR! %s no such directory" % options.out_neg_folder) + term_colors.ENDC
        sys.exit(0)
        

    neg_sample_num = 0
    cv_negative_list_file_name = options.cascade_classifier_name + "_train_negatives.dat"
    cv_negative_list_file = open(cv_negative_list_file_name, "w")

    for cv_mu_image in cv_mu_images:
        negative_mu_boxes = [e for e in cv_mu_image.mu_boxes if not e.positive_flag]

        path = cv_mu_image.path
        
        for nbox in negative_mu_boxes:
            # note: pil requires absolute coords for both corners
            descaled_coords = tuple([e * cv_mu_image.inv_scaling_factor for e in (nbox.tlx, nbox.tly, nbox.tlx+nbox.width, nbox.tly+nbox.heigth)])
            cropped_neg_sample = Image.open(path).crop(descaled_coords)
            cropped_neg_sample_name = os.path.join(options.out_neg_folder, "negative_%i.png" % neg_sample_num)
            cv_negative_list_file.write(cropped_neg_sample_name+"\n")
            cropped_neg_sample.save(cropped_neg_sample_name)
            neg_sample_num += 1
            print "%i/%i negatives saved" % (neg_sample_num, total_negatives_num)     
    cv_negative_list_file.close()
         
         
         
    # launch the opencv_createsamples command
    all_aspect_ratios = []

    for cv_mu_image in cv_mu_images:
        for mu_box in cv_mu_image.mu_boxes:
            all_aspect_ratios.append(mu_box.aspect_ratio())

    mean_aspect_ratio = np.mean(np.array(all_aspect_ratios))
      
    print "positive samples mean aspect ratio:", mean_aspect_ratio
    default_height = 24
    width = int(default_height * mean_aspect_ratio)
    height = default_height

    vec_file_name = options.cascade_classifier_name + ".vec"

    create_samples_command = "opencv_createsamples -vec %s -info %s -num %i -h %i -w %i -show" % (vec_file_name, options.positive_samples_list, total_positives_num, height, width)

    print "starting opencv_createsamples: [press ESC not to show samples]"
    print term_colors.OKBLUE + create_samples_command
    os.system(create_samples_command)
    print term_colors.ENDC
    # opencv_traincascade suggestion
    cascade_dir_name = options.cascade_classifier_name + "_output_xmls"
    if not os.path.isdir(cascade_dir_name):
        print "creating %s folder for possible output of opencv_traincascade" % cascade_dir_name
        os.mkdir(cascade_dir_name)

    numPos = int(0.85 * total_positives_num)

    traincascade_command = "opencv_traincascade -data %s -vec %s -bg %s -numPos %i -numNeg %i -numStages 20 -h %i -w %i" % (cascade_dir_name, vec_file_name, cv_negative_list_file_name, numPos, total_negatives_num, height, width)

    print "suggested opencv_traincascade command:"
    print term_colors.OKGREEN + traincascade_command + term_colors.ENDC

         
         
         
         
         
         
         
         
         
         
         
         
         
         
         
