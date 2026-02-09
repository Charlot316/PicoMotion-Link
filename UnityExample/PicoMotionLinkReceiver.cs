using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Collections.Generic;
using Autohand;

#if UNITY_EDITOR
public class PicoMotionLinkReceiver : MonoBehaviour
{
    public int port = 9000;
    
    private Hand leftHand;
    private HandCanvasPointer leftUIPointer;
    private Hand rightHand;
    private HandCanvasPointer rightUIPointer;
    
    private UdpClient udpClient;
    private Thread receiveThread;
    
    [System.Serializable]
    public class PicoButton {
        public bool pressed;
        public float value;
    }

    [System.Serializable]
    public class PicoData {
        public string type;
        public string handedness; 
        public Vector3 position;  
        public Quaternion orientation; 
        public List<PicoButton> buttons;
        public List<float> axes; // [x, y]
    }

    private PicoData leftDataCache;
    private PicoData rightDataCache;
    private PicoData headDataCache;
    private readonly object dataLock = new object();
    private float lastReceiveTime = 0;

    public bool IsReceiving {
        get { return Time.time - lastReceiveTime < 2f; }
    }


    // 按钮状态记录
    private bool lastLeftTrigger = false;
    private bool lastLeftGrip = false;
    private bool lastRightTrigger = false;
    private bool lastRightGrip = false;

    void Start() {
        InitializeHands();
        StartUDP();
    }

    void InitializeHands() {
        var hands = Object.FindObjectsOfType<Hand>();
        foreach (var hand in hands) {
            if (hand.left) {
                leftHand = hand;
                leftUIPointer = hand.GetComponentInChildren<HandCanvasPointer>();
            } else {
                rightHand = hand;
                rightUIPointer = hand.GetComponentInChildren<HandCanvasPointer>();
            }
        }
    }

    void StartUDP() {
        try {
            udpClient = new UdpClient(port);
            receiveThread = new Thread(new ThreadStart(ReceiveData));
            receiveThread.IsBackground = true;
            receiveThread.Start();
            Debug.Log($"[PicoLink] UDP Receiver started on port {port}");
        } catch (System.Exception e) {
            Debug.LogError($"[PicoLink] UDP Error: {e.Message}");
        }
    }

    void ReceiveData() {
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        while (true) {
            try {
                if (udpClient == null) break;
                byte[] data = udpClient.Receive(ref anyIP);
                if (data == null || data.Length == 0) continue;

                string json = Encoding.UTF8.GetString(data);
                
                var picoData = JsonUtility.FromJson<PicoData>(json);
                if (picoData != null) {
                    lock (dataLock) {
                        if (picoData.type == "controller") {
                            if (picoData.handedness == "left") leftDataCache = picoData;
                            else if (picoData.handedness == "right") rightDataCache = picoData;
                        } else if (picoData.type == "head") {
                            headDataCache = picoData;
                        }
                        lastReceiveTime = Time.time;
                    }
                }
            } catch {
                if (udpClient == null) break;
            }
        }
    }

    void Update() {
        // 仅处理按钮事件，位置同步移至 HandDesktopControllerLink
        lock (dataLock) {
            ProcessButtons(leftHand, leftUIPointer, leftDataCache, ref lastLeftTrigger, ref lastLeftGrip);
            ProcessButtons(rightHand, rightUIPointer, rightDataCache, ref lastRightTrigger, ref lastRightGrip);
        }
    }

    void ProcessButtons(Hand hand, HandCanvasPointer uiPointer, PicoData data, ref bool lastTrigger, ref bool lastGrip) {
        if (hand == null || data == null || data.buttons == null || data.buttons.Count < 2) return;

        // 标准 WebXR 映射：Index 0 为 Index Trigger, Index 1 为 Side Grip
        bool currentSqueezeBtn = data.buttons[0].pressed; 
        bool currentGrabBtn = data.buttons[1].pressed;    

        if (currentGrabBtn && !lastGrip) hand.Grab();
        else if (!currentGrabBtn && lastGrip) hand.Release();

        if (currentSqueezeBtn && !lastTrigger) {
            hand.Squeeze();
            if (uiPointer != null) uiPointer.Press();
        }
        else if (!currentSqueezeBtn && lastTrigger) {
            hand.Unsqueeze();
            if (uiPointer != null) uiPointer.Release();
        }

        lastTrigger = currentSqueezeBtn;
        lastGrip = currentGrabBtn;
    }

    public PicoData GetLatestData(bool isLeft) {
        lock (dataLock) {
            return isLeft ? leftDataCache : rightDataCache;
        }
    }

    public PicoData GetHeadData() {
        lock (dataLock) {
            return headDataCache;
        }
    }

    void OnApplicationQuit() {
        if (receiveThread != null && receiveThread.IsAlive) receiveThread.Abort();
        if (udpClient != null) {
            udpClient.Close();
            udpClient = null;
        }
    }
}
#else
public class PicoMotionLinkReceiver : MonoBehaviour { }
#endif
