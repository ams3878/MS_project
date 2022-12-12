# Mapping Faces: mocap to avatar using FACS

Files:
  - MappingClasses.py : file with the the class definitions and implmentation
    - Class FacialMapping - the base class of any mapping implementation
    - Class FACS(FacialMapping) - a mapping implemntation using FACS
  - mopcap.py : file that contains everythign pertaining to processing motion capture data
    - Class MoCapBaseClass - the base class of any mocap implementation
    - Class MoCap_openface(MoCapBaseClass) - an implementation for processing the landmarks gathered using openface/cv2/dlib
  - controls.py : file that contains everhting pertaining to processing avatar control data
    - Class ControlBaseClass - the base class of any controls implementation
    - Class ARkitControls(ControlBaseClass) - an implementation for mapping to ARKit and saving controls data to a file
 - Other : 
    - helpers.py - functions that are used for debugging
    - main.py - a script that runs the the pipeline in a loop.
    - camera.py - functions that get/modify the camera and image. mostly just wrappers cv2 calls
    - FACS_aus - a file contating the FACS info. number,name,muscles for parsing.
    - shape_predictor_81_face_landmarks.dat - the landmarks model that was used to predictions.
 - Required Libraries : 
   - cv2
   - dlib
   - numpy
   - tkinter
   - openface - this is the only tough install follow the instructions **[here]( https://cmusatyalab.github.io/openface/setup/)**
I found the easiest way was to just download the **[openface GIT](https://github.com/cmusatyalab/openface)** and put it in the workign directory.
