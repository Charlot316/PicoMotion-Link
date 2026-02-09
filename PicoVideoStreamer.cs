using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System;
using System.Collections.Generic;

namespace Autohand {
#if UNITY_EDITOR
    public class PicoVideoStreamer : MonoBehaviour
    {
        public Camera streamCamera;
        
        public enum StreamResolution { _720p, _1080p, _2K, _4K }
        public enum StreamingMode { Mono, Stereo }

        [Header("VSSP v1.0 Connection")]
        [Tooltip("留空则自动使用 127.0.0.1")]
        public string targetIP = "127.0.0.1";
        public int targetPort = 8789; 
        
        [Header("Stream Settings")]
        public StreamingMode streamMode = StreamingMode.Mono;
        public StreamResolution resolution = StreamResolution._1080p;
        [Range(0.000f, 0.200f)] public float ipd = 0.064f; 
        [Range(60f, 120f)] public float fieldOfView = 90f;
        public bool swapEyes = false;
        
        [Range(1, 100)] public int quality = 75;
        [Range(1, 60)] public float frameRate = 30f; 

        private UdpClient udpClient;
        private IPEndPoint remoteEndPoint;
        private RenderTexture renderTexture;
        private Texture2D texture;
        private float lastFrameTime;
        private HandDesktopControllerLink controllerLink;
        private uint currentFrameId = 0;

        private int currentWidth;
        private int currentHeight;

        void OnGUI() {
            GUILayout.BeginArea(new Rect(10, 100, 220, 520), GUI.skin.box);
            GUILayout.Label("<b>VSSP v1.0 (UDP Stream)</b>");
            GUILayout.Label("<color=cyan>Target: " + (string.IsNullOrEmpty(targetIP) ? "127.0.0.1" : targetIP) + "</color>");
            
            if (GUILayout.Button("Mode: " + streamMode.ToString())) {
                streamMode = (streamMode == StreamingMode.Mono ? StreamingMode.Stereo : StreamingMode.Mono);
            }
            if (GUILayout.Button("Res: " + resolution.ToString())) {
                resolution = (StreamResolution)(((int)resolution + 1) % 4);
            }
            GUILayout.Label($"FPS: {frameRate:F0} | Quality: {quality}");
            frameRate = GUILayout.HorizontalSlider(frameRate, 1f, 60f);
            quality = (int)GUILayout.HorizontalSlider(quality, 10, 100);

            if (streamMode == StreamingMode.Stereo) {
                GUILayout.Label($"IPD: {ipd * 1000:F0}mm | FOV: {fieldOfView:F0}");
                ipd = GUILayout.HorizontalSlider(ipd, 0, 0.2f);
                fieldOfView = GUILayout.HorizontalSlider(fieldOfView, 60, 120);
                swapEyes = GUILayout.Toggle(swapEyes, "Swap Eyes");
            }
            GUILayout.EndArea();
        }

        void Start() {
            if (string.IsNullOrEmpty(targetIP)) targetIP = "127.0.0.1";
            
            UpdateResolutionSettings();
            controllerLink = FindObjectOfType<HandDesktopControllerLink>();
            if (streamCamera == null) streamCamera = Camera.main;
            
            try {
                udpClient = new UdpClient();
                remoteEndPoint = new IPEndPoint(IPAddress.Parse(targetIP), targetPort);
                Debug.Log($"[VSSP] Started. Target: {targetIP}:{targetPort}");
                
                // 打印本机内网 IP，方便查阅
                foreach (var ip in Dns.GetHostEntry(Dns.GetHostName()).AddressList) {
                    if (ip.AddressFamily == AddressFamily.InterNetwork) {
                        Debug.Log("[VSSP] System Local IP: " + ip.ToString());
                    }
                }
            } catch (Exception e) {
                Debug.LogError("[VSSP] Socket Error: " + e.Message);
            }
        }

        void UpdateResolutionSettings() {
            int w = 720, h = 720;
            switch(resolution) {
                case StreamResolution._720p: w = 720; h = 720; break;
                case StreamResolution._1080p: w = 1080; h = 1080; break;
                case StreamResolution._2K: w = 1440; h = 1440; break;
                case StreamResolution._4K: w = 2160; h = 2160; break;
            }
            
            if (texture == null || w != currentWidth || h != currentHeight) {
                currentWidth = w; currentHeight = h;
                if(renderTexture != null) renderTexture.Release();
                renderTexture = new RenderTexture(currentWidth, currentHeight, 16, RenderTextureFormat.ARGB32);
                texture = new Texture2D(currentWidth, currentHeight, TextureFormat.RGB24, false);
            }
        }

        void LateUpdate() {
            if (Time.time - lastFrameTime < 1f / frameRate) return;
            lastFrameTime = Time.time;
            SendVSSPFrame();
        }

        void SendVSSPFrame() {
            try {
                if (streamCamera == null) {
                    streamCamera = Camera.main;
                    if (streamCamera == null) streamCamera = FindObjectOfType<Camera>();
                }
                if (streamCamera == null) return;

                UpdateResolutionSettings(); 
                if (renderTexture == null || texture == null) return;

                RenderTexture curRT = RenderTexture.active;
                streamCamera.targetTexture = renderTexture;
                streamCamera.fieldOfView = fieldOfView;
                streamCamera.rect = new Rect(0, 0, 1, 1);

                if (streamMode == StreamingMode.Mono) {
                    streamCamera.Render();
                    byte[] data = CaptureFrame();
                    if (data != null) SliceAndSend(data, 0, 0); 
                } else {
                    Vector3 originalPos = streamCamera.transform.localPosition;
                    
                    // 1. Render & Send Left Eye (ID = 1)
                    float offset = swapEyes ? (ipd / 2f) : -(ipd / 2f);
                    streamCamera.transform.localPosition = originalPos + Vector3.right * offset;
                    streamCamera.Render();
                    byte[] leftData = CaptureFrame();
                    if (leftData != null) SliceAndSend(leftData, 1, 1);
                    
                    // 2. Render & Send Right Eye (ID = 2)
                    offset = swapEyes ? -(ipd / 2f) : (ipd / 2f);
                    streamCamera.transform.localPosition = originalPos + Vector3.right * offset;
                    streamCamera.Render();
                    byte[] rightData = CaptureFrame();
                    if (rightData != null) SliceAndSend(rightData, 1, 2);
                    
                    streamCamera.transform.localPosition = originalPos;
                }
                
                streamCamera.targetTexture = null;
                RenderTexture.active = curRT;
                currentFrameId++;
            } catch (Exception e) {
                Debug.LogWarning("[VSSP] Render Error: " + e.Message);
            }
        }

        private byte[] CaptureFrame() {
            RenderTexture.active = renderTexture;
            texture.ReadPixels(new Rect(0, 0, currentWidth, currentHeight), 0, 0);
            texture.Apply();
            return texture.EncodeToJPG(quality);
        }

        private void SliceAndSend(byte[] frameData, byte mode, byte eye) {
            if (udpClient == null) return;
            const int MAX_PAYLOAD = 1200;
            int totalBytes = frameData.Length;
            ushort packetCount = (ushort)Mathf.CeilToInt((float)totalBytes / MAX_PAYLOAD);
            
            for (ushort i = 0; i < packetCount; i++) {
                int offset = i * MAX_PAYLOAD;
                int size = Math.Min(MAX_PAYLOAD, totalBytes - offset);
                
                byte[] packet = new byte[24 + size];
                
                // Pack Header (Little Endian)
                // 0: Magic 'VSSP'
                byte[] magic = System.Text.Encoding.ASCII.GetBytes("VSSP");
                Buffer.BlockCopy(magic, 0, packet, 0, 4);
                
                // 4: Frame ID
                Buffer.BlockCopy(BitConverter.GetBytes(currentFrameId), 0, packet, 4, 4);
                
                // 8, 9, 10, 11: mode, eye, codec, flags
                packet[8] = mode;
                packet[9] = eye;
                packet[10] = 0; // MJPEG (Custom extension for low-latency proof of concept)
                packet[11] = (byte)((i == packetCount - 1) ? 2 : 0); // bit1: last_packet
                
                // 12: Packet ID, 14: Packet Count, 16: Payload Size
                Buffer.BlockCopy(BitConverter.GetBytes(i), 0, packet, 12, 2);
                Buffer.BlockCopy(BitConverter.GetBytes(packetCount), 0, packet, 14, 2);
                Buffer.BlockCopy(BitConverter.GetBytes((ushort)size), 0, packet, 16, 2);
                
                // 18: Timestamp
                Buffer.BlockCopy(BitConverter.GetBytes((uint)(Time.time * 1000)), 0, packet, 18, 4);
                
                // 24 onwards: Payload
                Buffer.BlockCopy(frameData, offset, packet, 24, size);
                
                udpClient.Send(packet, packet.Length, remoteEndPoint);
            }
        }

        void OnDestroy() {
            if (udpClient != null) udpClient.Close();
            if (renderTexture != null) renderTexture.Release();
        }
    }
#else
    public class PicoVideoStreamer : MonoBehaviour { }
#endif
}
