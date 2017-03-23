# opencv_traincascade_toolchain

In order to train an OpenCV cascade classifier one needs a set of negative and positive samples
(see the [OpenCV User Guide](http://docs.opencv.org/2.4.13.2/doc/user_guide/ug_traincascade.html) ).
The creation of the necessary samples is simplified with this toolchain.

For a quick test on a GNU/Linux system:
```
python create_samples.py -i example_images -n apple -P positives.dat -N tool_negatives.dat -o negatives
```
drag-select positive samples with the cursor
use W and S keys to move to the next or previous image
\
![positive sample selection](docs/positive_sample.png?raw=true "positive sample selection")


in the end create_samples.py suggests an opencv_traincascade command which is consistent with the parameters relevant to the sets of samples that has been created:
```
opencv_traincascade -data apple_output_xmls -vec apple.vec -bg apple_train_negatives.dat -numPos 5 -numNeg 9 -num 20 -h 24 -w 26
```
