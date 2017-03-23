# opencv_traincascade_toolchain

In order to train an OpenCV cascade classifier one needs a set of negative and positive samples
(see the [OpenCV User Guide](http://docs.opencv.org/2.4.13.2/doc/user_guide/ug_traincascade.html) ).
The creation of the necessary samples is simplified with this toolchain.

For a quick test on a GNU/Linux system:
```
git clone https://github.com/wolf32d/opencv_traincascade_toolchain/edit/master/README.md
cd opencv_traincascade_toolchain
mkdir negatives
python create_samples.py -i example_images -n apple -P positives.dat -N tool_negatives.dat -o negatives
```
\
drag-select positive samples with the cursor
use W and S keys to move to the next or previous image
\
![positive sample selection](docs/positive_sample.png?raw=true "positive sample selection")
\
hit the P key to toggle between positive and negative samples selection, hit BACKSPACE or DELETE to delete the smaples in the current image
\
![positive sample selection](docs/negative_samplel.png?raw=true "negative sample selection")

you can pick multiple samples multiple from the same image
\
![multiple samples](docs/multiple_samples.png?raw=true "multiple samples selection")
\
When you have selected enpugh samples just quit the image window. The coordinates of both the green and red boxes (positive and negative samples) will be saved in the two files specified with the -P and -N options. 

The script create_samples.py will then suggest an opencv_traincascade command which is consistent with the parameters relevant to the sets of samples that has been created. Here's an example:
\
```
opencv_traincascade -data apple_output_xmls -vec apple.vec -bg apple_train_negatives.dat -numPos 5 -numNeg 9 -num 20 -h 24 -w 26
```
