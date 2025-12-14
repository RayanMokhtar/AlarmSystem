#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <iostream>
#include <fstream>

using namespace cv;
using namespace dnn;
using namespace std;

int main() {
    // Charger noms de classes
    vector<string> classes;
    ifstream f("YoloUtils/coco.names");
    string line;
    while (getline(f, line)) classes.push_back(line);

    // Charger YOLOv3
    Net net = readNet("YoloUtils/yolov3.weights", "YoloUtils/yolov3.cfg");
    net.setPreferableBackend(DNN_BACKEND_OPENCV);
    net.setPreferableTarget(DNN_TARGET_CPU);

    VideoCapture cap(0);
    if (!cap.isOpened()) return -1;

    Mat frame;
    while (true) {
        cap >> frame;
        if (frame.empty()) break;

        // Prétraitement YOLOv3
        Mat blob;
        blobFromImage(frame, blob, 1/255.0, Size(320,320), Scalar(), true, false);
        net.setInput(blob);

        // Forward sur toutes les couches de sortie
        vector<Mat> outs;
        net.forward(outs, net.getUnconnectedOutLayersNames());

        vector<int> classIds;
        vector<float> confidences;
        vector<Rect> boxes;

        for (auto &out : outs) {
            float *data = (float*)out.data;
            for (int i = 0; i < out.rows; i++, data += out.cols) {
                float conf = data[4];
                if (conf > 0.5) {
                    float *scores = data + 5;
                    Point classIdPoint;
                    double maxVal;
                    minMaxLoc(Mat(1, classes.size(), CV_32F, scores), 0, &maxVal, 0, &classIdPoint);

                    if (maxVal > 0.5) {
                        int cx = data[0] * frame.cols;
                        int cy = data[1] * frame.rows;
                        int w  = data[2] * frame.cols;
                        int h  = data[3] * frame.rows;
                        int left = cx - w/2;
                        int top  = cy - h/2;

                        boxes.push_back(Rect(left, top, w, h));
                        confidences.push_back(maxVal);
                        classIds.push_back(classIdPoint.x);
                    }
                }
            }
        }

        // Suppression des doublons
        vector<int> indices;
        NMSBoxes(boxes, confidences, 0.5, 0.4, indices);

        for (int i : indices) {
            rectangle(frame, boxes[i], Scalar(0,255,0), 2);
            putText(frame, classes[classIds[i]], Point(boxes[i].x, boxes[i].y-5),
                    FONT_HERSHEY_SIMPLEX, 0.5, Scalar(0,255,0), 2);
        }

        imshow("YOLOv3 Webcam", frame);
        if (waitKey(1) == 27) break;
    }

    return 0;
}
