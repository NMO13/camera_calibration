import os
import cv2.aruco as aruco
import numpy as np
import cv2
import matplotlib.pyplot as plt

chessboard_size = (6, 4)

def draw_image_pair(frame_left, frame_right):
    numpy_horizontal_concat = np.concatenate((frame_left, frame_right), axis=1)
    cv2.imshow("0", numpy_horizontal_concat)
    cv2.waitKey(1)

def drawlines(img1,img2,lines,pts1,pts2):
    ''' img1 - image on which we draw the epilines for the points in img2
        lines - corresponding epilines
        code from OpenCV documentation
        '''
    r,c = img1.shape
    img1 = cv2.cvtColor(img1,cv2.COLOR_GRAY2BGR)
    img2 = cv2.cvtColor(img2,cv2.COLOR_GRAY2BGR)
    for r,pt1,pt2 in zip(lines,pts1,pts2):
        color = tuple(np.random.randint(0,255,3).tolist())
        x0,y0 = map(int, [0, -r[2]/r[1] ])
        x1,y1 = map(int, [c, -(r[2]+r[0]*c)/r[1] ])
        img1 = cv2.line(img1, (x0,y0), (x1,y1), color,1)
        img1 = cv2.circle(img1,tuple(pt1),5,color,-1)
        img2 = cv2.circle(img2,tuple(pt2),5,color,-1)
    return img1,img2

def draw_epilines(pts1, pts2, F, img1, img2):
    ''''
    code from OpenCV documentation
    '''
    lines1 = cv2.computeCorrespondEpilines(pts2.reshape(-1,1,2), 2,F)
    lines1 = lines1.reshape(-1,3)
    img5,img6 = drawlines(img1,img2,lines1,pts1,pts2)
    # Find epilines corresponding to points in left image (first image) and
    # drawing its lines on right image
    lines2 = cv2.computeCorrespondEpilines(pts1.reshape(-1,1,2), 1,F)
    lines2 = lines2.reshape(-1,3)
    img3,img4 = drawlines(img2,img1,lines2,pts2,pts1)
    plt.subplot(121),plt.imshow(img5)
    plt.subplot(122),plt.imshow(img3)
    plt.show()

def calibrate(image_points_left, image_points_right, image_size, object_points):
    ## Calibrate cameras
    (cam_mats, dist_coefs, rect_trans, proj_mats, valid_boxes,
     undistortion_maps, rectification_maps) = {}, {}, {}, {}, {}, {}, {}
    criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS,
                100, 1e-5)
    flags = (cv2.CALIB_FIX_ASPECT_RATIO + cv2.CALIB_ZERO_TANGENT_DIST +
             cv2.CALIB_SAME_FOCAL_LENGTH)
    (ret, cam_mats["left"], dist_coefs["left"], cam_mats["right"],
     dist_coefs["right"], rot_mat, trans_vec, e_mat,
     f_mat) = cv2.stereoCalibrate(object_points,
                                  image_points_left, image_points_right, None, None, None, None,
                                  image_size, criteria=criteria, flags=flags)

    print('error: {}'.format(ret))
    return f_mat

if __name__ == "__main__":
    from os import walk

    f = {}
    run = "./runs/run2/"
    for file in os.listdir(run):
        f[file] = file

    ######### find corners
    marker_length = 2.7
    square_length = 3.2
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_1000)
    board = aruco.CharucoBoard_create(5, 7, square_length, marker_length, aruco_dict)
    arucoParams = aruco.DetectorParameters_create()

    object_points = np.zeros((np.prod(chessboard_size), 3), dtype=np.float32)
    object_points[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

    corners_list_left, corners_list_right, objpts = [], [], []
    images_left, images_right = [], []

    for counter in range(int(len(f)/2)):
        img_left = cv2.imread(run + f["myleft{}.png".format(counter)], 0)
        img_right = cv2.imread(run + f["myright{}.png".format(counter)], 0)

        ### find corners in left image
        corners_left, ids_left, rejected = aruco.detectMarkers(
            img_left,
            aruco_dict,
            parameters=arucoParams
        )
        resp_left, charuco_corners_left, charuco_ids_left = aruco.interpolateCornersCharuco(
            markerCorners=corners_left,
            markerIds=ids_left,
            image=img_left,
            board=board
        )
        corners_list_left.append(charuco_corners_left.reshape(-1, 2))
        images_left.append(img_left)

        ### find corners in right image
        corners_right, ids_right, rejected = aruco.detectMarkers(
            img_right,
            aruco_dict,
            parameters=arucoParams
        )
        resp_right, charuco_corners_right, charuco_ids_right = aruco.interpolateCornersCharuco(
            markerCorners=corners_right,
            markerIds=ids_right,
            image=img_right,
            board=board
        )
        corners_list_right.append(charuco_corners_right.reshape(-1, 2))
        images_right.append(img_right)

        ### save 3D object points
        objpts.append(object_points)

        draw_image_pair(img_left, img_right)

    ######### find fundamental matrix F
    F = calibrate(corners_list_left, corners_list_right, img_left.shape, objpts)

    draw_epilines(np.int32(corners_list_left[1]), np.int32(corners_list_right[1]), F, images_left[1],
                  images_right[1])
