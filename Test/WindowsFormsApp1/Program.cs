using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.IO.Ports;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WindowsFormsApp1
{
    static class Program
    {
        static async Task WaitOk(SerialPort port)
        {
            while (port.BytesToRead == 0)
            {
                await Task.Delay(1);
            }
            var line = port.ReadLine();
            Console.WriteLine(line);
            if (!line.Contains("OK"))
            {
                await WaitOk(port);
            }
        }
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        
        static async Task Main()
        {
            Bitmap bmp = new Bitmap("D:\\1.png");
            SerialPort port = new SerialPort("COM3", 38400);
            port.Open();
            await Task.Delay(100);
            while (port.BytesToRead > 0)
            { 
                byte[] b = new byte[1];
                port.Read(b, 0, 1);
            }
            byte[] line = new byte[] { 42, 5, 16};
            byte[] fire = new byte[] { 42, 2, 4};
            //byte[] fire = new byte[] { 42, 2, 4, 10, 25, 0, 0 };
            byte[] scroll = new byte[] { 42, 4, 4, 2, 0, 0, 0 };
            for (int i = 0; i < bmp.Height; ++i)
            {
                byte[] grays = new byte[128];
                HashSet<byte> levels = new HashSet<byte>();
                for (int x = 0; x < 128; ++ x)
                {
                    grays[x] = (byte)Math.Round((1 - bmp.GetPixel(x, i).GetBrightness()) * 15);
                    levels.Add(grays[x]);
                }

                foreach (byte level in levels)
                {
                    if (level == 0)
                    {
                        continue;
                    }
                    byte[] thisLevel = grays.Select(x => (byte)(x == level ? x : 0)).ToArray();
                    byte[] bmpLine = new byte[16];
                    int ptr = 0;
                    for (int j = 15; j >= 0; --j)
                    {
                        for (int k = 0; k < 8; ++k)
                        {
                            bool value = thisLevel[ptr] > 0;
                            bmpLine[j] |= (byte)((value ? 1 : 0) << (k));
                            ++ptr;
                        }
                    }
                    port.Write(line, 0, line.Length);
                    port.Write(bmpLine, 0, bmpLine.Length);
                    await WaitOk(port);
                    port.Write(fire, 0, fire.Length);
                    port.Write(BitConverter.GetBytes((UInt32)(level / 16.0 * 6000.0+1000)), 0, 4);
                    await WaitOk(port);

                }

/*                byte[] bmpLine = new byte[16];
                int ptr = 0;
                for (int j = 15; j >= 0; --j)
                {
                    for (int k = 0; k < 8; ++k)
                    {
                        bool value = bmp.GetPixel(ptr, i).GetBrightness() < 0.5;
                        bmpLine[j] |= (byte)((value ? 1 : 0) << (k));
                        ++ptr;
                    }
                }
                port.Write(line, 0, line.Length);
                port.Write(bmpLine, 0, bmpLine.Length);
                await WaitOk(port);
                port.Write(fire, 0, fire.Length);
                await WaitOk(port);*/
                port.Write(scroll, 0, scroll.Length);
                await WaitOk(port);

            }
            port.Dispose();
        }
    }
}
