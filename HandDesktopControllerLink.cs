using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Autohand
{
#if UNITY_EDITOR
    [RequireComponent(typeof(PicoMotionLinkReceiver))]
    public class HandDesktopControllerLink : MonoBehaviour
    {
        [Header("Input References")]
        public Hand handRight;
        public Transform handRightFollow;
        public Hand handLeft;
        public Transform handLeftFollow;
        [Space]
        public Camera headCamera;
        public Transform trackingContainer;
        [Space]
        public AutoHandPlayer player;
        
        [Header("Pico Motion Link")]
        public bool usePicoLink = true;
        public bool useHmdRotation = true; // 新增：是否使用头显数据
        public PicoMotionLinkReceiver picoReceiver;
        public float picoPositionScale = 2.0f;
        public float rotationSpeed = 2.0f;

        private Vector3 leftInitialLocalPos;
        private Vector3 rightInitialLocalPos;
        private bool initializedInitialPos = false;

        private float xRotation = 0f;
        private float yRotation = 0f;

        private void Awake()
        {
            if (handRight != null) handRight.follow = handRightFollow;
            if (handLeft != null) handLeft.follow = handLeftFollow;

            picoReceiver = GetComponent<PicoMotionLinkReceiver>();
            
            // 记录双手的初始本地位置
            if (handLeftFollow != null) leftInitialLocalPos = handLeftFollow.localPosition;
            if (handRightFollow != null) rightInitialLocalPos = handRightFollow.localPosition;
            initializedInitialPos = true;

            // 初始化视角角度
            if (trackingContainer != null) yRotation = trackingContainer.localEulerAngles.y;
            if (headCamera != null) xRotation = headCamera.transform.localEulerAngles.x;

            if (player != null && headCamera != null) {
                player.forwardFollow = headCamera.transform;
            }
        }

        void Update()
        {
            if (!usePicoLink || picoReceiver == null) return;
            HandlePicoInput();
        }

        void HandlePicoInput() {
            float h = 0;
            float v = 0;

            // 1. 获取左手手柄数据 (控制移动 + 左手位置)
            var leftData = picoReceiver.GetLatestData(true);
            if (leftData != null) {
                if (leftData.axes != null && leftData.axes.Count >= 2) {
                    h = -leftData.axes[0];
                    v = leftData.axes[1]; 
                    if (Mathf.Abs(h) < 0.1f) h = 0;
                    if (Mathf.Abs(v) < 0.1f) v = 0;
                }
                
                if (handLeftFollow != null) {
                    Vector3 offset = new Vector3(leftData.position.x, leftData.position.y, -leftData.position.z) * picoPositionScale;
                    handLeftFollow.localPosition = offset;
                    handLeftFollow.localRotation = new Quaternion(-leftData.orientation.x, -leftData.orientation.y, leftData.orientation.z, leftData.orientation.w);

                    if(handLeft != null && handLeft.handFollow != null) {
                        handLeft.handFollow.SetMoveTo(true);
                    }
                }
            }

            // 2. 获取头部 HMD 数据 (真正的视角同步)
            var headData = picoReceiver.GetHeadData();
            if (headData != null && useHmdRotation) { // 增加开关判断
                if (headCamera != null) {
                    headCamera.transform.localRotation = new Quaternion(-headData.orientation.x, -headData.orientation.y, headData.orientation.z, headData.orientation.w);
                }
            }

            // 3. 获取右手手柄数据 (控制视角兜底 + 右手位置)
            var rightData = picoReceiver.GetLatestData(false);
            if (rightData != null) {
                if (rightData.axes != null && rightData.axes.Count >= 2) {
                    float rawLookX = rightData.axes[0];
                    float rawLookY = rightData.axes[1];

                    // 左右转身始终启用
                    if (Mathf.Abs(rawLookX) > 0.1f) {
                        yRotation += rawLookX * rotationSpeed * 0.5f;
                        if (trackingContainer != null) trackingContainer.localRotation = Quaternion.Euler(0f, yRotation, 0f);
                    }

                    // 上下看：如果不使用 HMD 数据，则启用摇杆控制
                    if (!useHmdRotation || headData == null) {
                        if (Mathf.Abs(rawLookY) > 0.1f) {
                            // 修正：Unity X轴旋转正值为向下看，上推摇杆(v>0)时应减小X值以向上看
                            xRotation -= rawLookY * rotationSpeed * 1.5f; 
                            xRotation = Mathf.Clamp(xRotation, -80f, 80f);
                            if (headCamera != null) headCamera.transform.localRotation = Quaternion.Euler(xRotation, 0f, 0f);
                        }
                    }
                }

                if (handRightFollow != null) {
                    Vector3 offset = new Vector3(rightData.position.x, rightData.position.y, -rightData.position.z) * picoPositionScale;
                    handRightFollow.localPosition = offset;
                    handRightFollow.localRotation = new Quaternion(-rightData.orientation.x, -rightData.orientation.y, rightData.orientation.z, rightData.orientation.w);

                    if(handRight != null && handRight.handFollow != null) {
                        handRight.handFollow.SetMoveTo(true);
                    }
                }
            }

            if (player != null) {
                if (h == 0 && v == 0) {
                    player.Move(Vector2.zero);
                    if (player.body != null) {
                        Vector3 vel = player.body.velocity;
                        vel.x = 0; vel.z = 0;
                        player.body.velocity = vel;
                    }
                } else {
                    // 使用经过翻转处理后的 h 和 v (h = -axes[0], v = axes[1])
                    // 传给 AutoHandPlayer，它内部会根据 forwardFollow (Camera) 自动旋转到世界坐标
                    player.Move(new Vector2(h, v), false);
                }
            }
        }

        private void OnGUI() {
            GUI.Box(new Rect(10, 10, 250, 80), "PICO Controller Integration");
            GUI.Label(new Rect(20, 30, 230, 20), "Pure 6DOF Mode (No Keyboard/Mouse)");
            useHmdRotation = GUI.Toggle(new Rect(20, 50, 230, 20), useHmdRotation, " Use HMD Rotation Sync");
        }
    }
#else
    public class HandDesktopControllerLink : MonoBehaviour { }
#endif
}
