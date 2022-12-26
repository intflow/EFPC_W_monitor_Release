#!/bin/bash

# opencv 삭제
echo -e "\nDELETE OPENCV\n"
sudo apt purge libopencv* python-opencv -y && \
sudo apt autoremove -y
sudo find /usr/local/ -name "*opencv*" -exec rm -rf {} \;

echo -e "\n\nIntsall dependency!\n"
# dependency 설치
sudo apt update -y && \
sudo apt install -y \
build-essential \
cmake \
pkg-config \
libjpeg-dev \
libtiff5-dev \
libpng-dev \
libavcodec-dev \
libavformat-dev \
libswscale-dev \
libxvidcore-dev \
libx264-dev \
x264 \
libxine2-dev \
libv4l-dev \
v4l-utils \
qv4l2 \
v4l2ucp \
libgstreamer1.0-dev \
libgstreamer-plugins-base1.0-dev \
libgstreamer-plugins-good1.0-dev \
libgtk2.0-dev \
libgtk-3-dev \
libqt4-dev \
qt5-default \
mesa-utils \
libgl1-mesa-dri \
libqt4-opengl-dev \
libgtkgl2.0-dev \
libgtkglext1-dev \
libtbb2 \
libtbb-dev \
libatlas-base-dev \
gfortran \
libeigen3-dev \
python2.7-dev \
python3-dev \
python-numpy \
python3-numpy \
python3-setuptools \
zip \
unzip \
wget

# opencv 다운로드
cd /
sudo mkdir -p opencv
if [ -d "/opencv" ]; then
    echo -e "\n\n Download OpenCV"
    cd opencv
    sudo wget -O opencv.zip https://github.com/opencv/opencv/archive/4.5.1.zip && \
    sudo unzip opencv.zip

    sudo wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.5.1.zip && \
    sudo unzip opencv_contrib.zip

    # build 준비
    if [ -d "opencv-4.5.1" ] && [ -d "opencv_contrib-4.5.1" ]; then
        cd opencv-4.5.1/
        sudo mkdir -p build
        cd build

        # build
        echo -e "\n\nBUILD!\n"
        sudo cmake \
        -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-4.5.1/modules \
        -D BUILD_opencv_python2=ON \
        -D BUILD_opencv_python3=ON \
        -D WITH_CUDA=ON \
        -D WITH_CUDNN=ON \
        -D CUDA_FAST_MATH=ON \
        -D CUDNN_VERSION='8.0' \
        -D OPENCV_DNN_CUDA=OFF \
        -D WITH_GSTREAMER=ON \
        -D WITH_LIBV4L=ON \
        -D WITH_OPENGL=ON \
        -D WITH_CUBLAS=ON \
        -D ENABLE_NEON=ON \
        -D OPENCV_ENABLE_NONFREE=ON \
        -D OPENCV_GENERATE_PKGCONFIG=ON \
        -D EIGEN_INCLUDE_PATH=/usr/include/eigen3 \
        \
        -D INSTALL_C_EXAMPLES=ON \
        -D INSTALL_PYTHON_EXAMPLES=ON \
        -D BUILD_NEW_PYTHON_SUPPORT=ON \
        -D BUILD_WITH_DEBUG_INFO=OFF \
        -D BUILD_DOCS=OFF \
        -D BUILD_EXAMPLES=OFF \
        -D BUILD_TESTS=OFF \
        -D BUILD_PERF_TESTS=OFF \
        \
        -D WITH_TBB=ON \
        -D WITH_IPP=OFF \
        -D WITH_1394=OFF \
        -D WITH_QT=OFF \
        -D WITH_GTK=ON \
        -D WITH_FFMPEG=ON \
        -D WITH_XINE=ON \
        ../

        time sudo make -j4 && \
        sudo make install && \
        sudo rm -rf /opencv

        # 설치 확인
        opencv_version --verbose
    fi
else
    echo "no such directory : /opencv"
fi

