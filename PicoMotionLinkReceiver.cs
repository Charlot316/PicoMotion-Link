using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class PicoMotionLinkReceiver : MonoBehaviour
{
    public int port = 9000;
    public Transform leftHand;
    public Transform rightHand;
    
    struct ControllerData {
        public string side;
        public Vector3 rel_pos;
        public Quaternion rot;
    }

    UdpClient udpClient;
    Thread receiveThread;
    string lastJson = "";

    void Start() {
        udpClient = new UdpClient(port);
        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveData() {
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        while (true) {
            try {
                byte[] data = udpClient.Receive(ref anyIP);
                lastJson = Encoding.UTF8.GetString(data);
            } catch { }
        }
    }

    void Update() {
        if (string.IsNullOrEmpty(lastJson)) return;

        // 解析 Python 传来的 JSON
        // 注意：这里需要你定义对应的 JSON 结构体或使用 SimpleJSON
        var data = JsonUtility.FromJson<PicoData>(lastJson);
        
        Transform target = data.side == "left" ? leftHand : rightHand;
        if (target != null) {
            // 注意：WebXR 的坐标系和 Unity 略有不同，可能需要 Z 轴翻转
            target.localPosition = new Vector3(data.pos.x, data.pos.y, -data.pos.z);
            target.localRotation = new Quaternion(data.rot.x, data.rot.y, data.rot.z, data.rot.w);
        }
    }

    [System.Serializable]
    public class PicoData {
        public string side;
        public Vector3 pos;
        public Quaternion rot;
    }

    void OnApplicationQuit() {
        if (receiveThread != null) receiveThread.Abort();
        if (udpClient != null) udpClient.Close();
    }
}
