# Valorant Color Grade
# Kym je toto okno otvorene -> farby su "hernne" (vibrance + kontrast).
# Ked okno zavries -> vsetko sa vrati presne tak, ako to bolo predtym.
#
# Spustaj cez "Spustit ColorGrade.bat" (dvojklik).

$ErrorActionPreference = 'Stop'

$source = @'
using System;
using System.IO;
using System.Text;
using System.Drawing;
using System.Globalization;
using System.Collections.Generic;
using System.Windows.Forms;
using System.Runtime.InteropServices;

// ---------------------------------------------------------------- NVIDIA vibrance (NVAPI)
public static class NvVibrance
{
    [DllImport("nvapi64.dll", EntryPoint = "nvapi_QueryInterface", CallingConvention = CallingConvention.Cdecl)]
    static extern IntPtr QueryInterface64(uint id);
    [DllImport("nvapi.dll", EntryPoint = "nvapi_QueryInterface", CallingConvention = CallingConvention.Cdecl)]
    static extern IntPtr QueryInterface32(uint id);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int InitFn();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int EnumDisplayFn(int index, out IntPtr handle);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int GetDvcFn(IntPtr handle, uint outputId, ref DvcInfo info);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int SetDvcFn(IntPtr handle, uint outputId, int level);

    [StructLayout(LayoutKind.Sequential)]
    struct DvcInfo { public uint version; public int current; public int min; public int max; }

    static EnumDisplayFn enumDisplay;
    static GetDvcFn getDvc;
    static SetDvcFn setDvc;
    static readonly List<IntPtr> displays = new List<IntPtr>();

    public static bool Available { get; private set; }

    static T Fn<T>(uint id) where T : class
    {
        IntPtr p = IntPtr.Size == 8 ? QueryInterface64(id) : QueryInterface32(id);
        if (p == IntPtr.Zero) return null;
        return Marshal.GetDelegateForFunctionPointer(p, typeof(T)) as T;
    }

    public static void Init()
    {
        try
        {
            InitFn init = Fn<InitFn>(0x0150E828);
            enumDisplay = Fn<EnumDisplayFn>(0x9ABDD40D);
            getDvc = Fn<GetDvcFn>(0x4085DE45);
            setDvc = Fn<SetDvcFn>(0x172409B4);
            if (init == null || enumDisplay == null || getDvc == null || setDvc == null || init() != 0) return;
            for (int i = 0; i < 16; i++)
            {
                IntPtr h;
                if (enumDisplay(i, out h) != 0) break;
                displays.Add(h);
            }
            Available = displays.Count > 0;
        }
        catch (Exception) { Available = false; } // nie je NVIDIA karta / driver
    }

    static DvcInfo Info(IntPtr h)
    {
        DvcInfo info = new DvcInfo();
        info.version = (uint)Marshal.SizeOf(typeof(DvcInfo)) | (1u << 16);
        getDvc(h, 0, ref info);
        return info;
    }

    public static int[] GetLevels()
    {
        int[] r = new int[displays.Count];
        for (int i = 0; i < displays.Count; i++) r[i] = Info(displays[i]).current;
        return r;
    }

    public static void SetLevels(int[] levels)
    {
        for (int i = 0; i < displays.Count && i < levels.Length; i++) setDvc(displays[i], 0, levels[i]);
    }

    // percent = to iste cislo ako "Digital Vibrance" v NVIDIA Control Panel (50 = default, 100 = max)
    public static void SetPercent(int percent)
    {
        foreach (IntPtr h in displays)
        {
            DvcInfo info = Info(h);
            int level = (int)Math.Round((Math.Max(50, Math.Min(100, percent)) - 50) / 50.0 * info.max);
            setDvc(h, 0, level);
        }
    }
}

// ---------------------------------------------------------------- Gamma ramp (kontrast / gamma / jas, funguje na kazdej GPU)
public static class Gamma
{
    [DllImport("gdi32.dll")] static extern bool SetDeviceGammaRamp(IntPtr hdc, ushort[] ramp);
    [DllImport("gdi32.dll")] static extern bool GetDeviceGammaRamp(IntPtr hdc, ushort[] ramp);
    [DllImport("gdi32.dll", CharSet = CharSet.Unicode)] static extern IntPtr CreateDC(string driver, string device, string output, IntPtr init);
    [DllImport("gdi32.dll")] static extern bool DeleteDC(IntPtr hdc);

    public static string[] Monitors()
    {
        Screen[] s = Screen.AllScreens;
        string[] r = new string[s.Length];
        for (int i = 0; i < s.Length; i++) r[i] = s[i].DeviceName;
        return r;
    }

    public static ushort[] Get(string monitor)
    {
        ushort[] ramp = new ushort[768];
        IntPtr dc = CreateDC(null, monitor, null, IntPtr.Zero);
        try { if (!GetDeviceGammaRamp(dc, ramp)) return null; }
        finally { DeleteDC(dc); }
        return ramp;
    }

    public static bool Set(string monitor, ushort[] ramp)
    {
        IntPtr dc = CreateDC(null, monitor, null, IntPtr.Zero);
        try { return SetDeviceGammaRamp(dc, ramp); }
        finally { DeleteDC(dc); }
    }

    public static ushort[] Build(double contrast, double gamma, double brightness)
    {
        ushort[] ramp = new ushort[768];
        for (int i = 0; i < 256; i++)
        {
            double x = i / 255.0;
            x = (x - 0.5) * contrast + 0.5 + brightness;
            x = Math.Max(0, Math.Min(1, x));
            x = Math.Pow(x, 1.0 / gamma);
            ushort v = (ushort)Math.Round(x * 65535);
            ramp[i] = v; ramp[256 + i] = v; ramp[512 + i] = v;
        }
        return ramp;
    }

    public static ushort[] Linear() { return Build(1, 1, 0); }
}

// ---------------------------------------------------------------- Nastavenia + zaloha povodneho stavu
public class Settings
{
    public int Vibrance = 80;     // 50..100  (NVIDIA Control Panel %)
    public int Contrast = 110;    // 100..140 (%)
    public int Gamma = 100;       // 70..130  (1.00 = bez zmeny)
    public int Brightness = 0;    // -10..10

    static string Dir { get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ValorantColorGrade"); } }
    static string FilePath { get { return Path.Combine(Dir, "settings.ini"); } }

    public static Settings Load()
    {
        Settings s = new Settings();
        if (!File.Exists(FilePath)) return s;
        foreach (string line in File.ReadAllLines(FilePath))
        {
            string[] kv = line.Split('=');
            int v;
            if (kv.Length != 2 || !int.TryParse(kv[1].Trim(), out v)) continue;
            switch (kv[0].Trim())
            {
                case "Vibrance": s.Vibrance = v; break;
                case "Contrast": s.Contrast = v; break;
                case "Gamma": s.Gamma = v; break;
                case "Brightness": s.Brightness = v; break;
            }
        }
        return s;
    }

    public void Save()
    {
        Directory.CreateDirectory(Dir);
        File.WriteAllLines(FilePath, new string[] {
            "Vibrance=" + Vibrance, "Contrast=" + Contrast, "Gamma=" + Gamma, "Brightness=" + Brightness });
    }
}

// Povodny stav sa zapise aj na disk. Ak by program spadol / vypol sa PC,
// pri dalsom spusteni sa najprv obnovi z tejto zalohy.
public static class Backup
{
    static string FilePath { get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ValorantColorGrade", "backup.txt"); } }

    public static int[] Vibrance;
    public static Dictionary<string, ushort[]> Ramps = new Dictionary<string, ushort[]>();

    public static void Capture()
    {
        Vibrance = NvVibrance.Available ? NvVibrance.GetLevels() : null;
        Ramps.Clear();
        foreach (string m in Gamma.Monitors())
        {
            ushort[] r = Gamma.Get(m);
            if (r != null) Ramps[m] = r;
        }
        Write();
    }

    static void Write()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(FilePath));
        List<string> lines = new List<string>();
        if (Vibrance != null)
        {
            string[] parts = new string[Vibrance.Length];
            for (int i = 0; i < Vibrance.Length; i++) parts[i] = Vibrance[i].ToString(CultureInfo.InvariantCulture);
            lines.Add("vibrance|" + string.Join(",", parts));
        }
        foreach (KeyValuePair<string, ushort[]> kv in Ramps)
        {
            byte[] bytes = new byte[kv.Value.Length * 2];
            Buffer.BlockCopy(kv.Value, 0, bytes, 0, bytes.Length);
            lines.Add("ramp|" + kv.Key + "|" + Convert.ToBase64String(bytes));
        }
        File.WriteAllLines(FilePath, lines.ToArray());
    }

    // true ak existovala zaloha z minuleho (spadnuteho) spustenia
    public static bool LoadLeftover()
    {
        if (!File.Exists(FilePath)) return false;
        Vibrance = null;
        Ramps.Clear();
        foreach (string line in File.ReadAllLines(FilePath))
        {
            string[] p = line.Split('|');
            if (p[0] == "vibrance" && p.Length == 2)
            {
                string[] nums = p[1].Split(',');
                Vibrance = new int[nums.Length];
                for (int i = 0; i < nums.Length; i++) Vibrance[i] = int.Parse(nums[i], CultureInfo.InvariantCulture);
            }
            else if (p[0] == "ramp" && p.Length == 3)
            {
                byte[] bytes = Convert.FromBase64String(p[2]);
                ushort[] ramp = new ushort[bytes.Length / 2];
                Buffer.BlockCopy(bytes, 0, ramp, 0, bytes.Length);
                Ramps[p[1]] = ramp;
            }
        }
        return true;
    }

    public static void Restore()
    {
        try { if (NvVibrance.Available && Vibrance != null) NvVibrance.SetLevels(Vibrance); } catch (Exception) { }
        foreach (string m in Gamma.Monitors())
        {
            ushort[] r;
            try { Gamma.Set(m, Ramps.TryGetValue(m, out r) ? r : Gamma.Linear()); } catch (Exception) { }
        }
        try { File.Delete(FilePath); } catch (Exception) { }
    }
}

// ---------------------------------------------------------------- Okno
public class ColorGradeForm : Form
{
    Settings settings = Settings.Load();
    Label status = new Label();
    Timer reapply = new Timer();
    bool restored;

    public ColorGradeForm()
    {
        Text = "Valorant Color Grade";
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(15, 25, 35);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10f);
        ClientSize = new Size(380, 330);

        Label title = new Label();
        title.Text = "COLOR GRADE: ZAPNUTÝ";
        title.Font = new Font("Segoe UI", 15f, FontStyle.Bold);
        title.ForeColor = Color.FromArgb(255, 70, 85);
        title.AutoSize = true;
        title.Location = new Point(16, 12);
        Controls.Add(title);

        status.AutoSize = false;
        status.Size = new Size(350, 40);
        status.Location = new Point(16, 46);
        status.ForeColor = Color.FromArgb(170, 180, 190);
        Controls.Add(status);

        int y = 92;
        AddSlider("Vibrance (NVIDIA %)", 50, 100, settings.Vibrance, ref y, delegate(int v) { settings.Vibrance = v; }, NvVibrance.Available);
        AddSlider("Kontrast %", 100, 140, settings.Contrast, ref y, delegate(int v) { settings.Contrast = v; }, true);
        AddSlider("Gamma (x100)", 70, 130, settings.Gamma, ref y, delegate(int v) { settings.Gamma = v; }, true);
        AddSlider("Jas", -10, 10, settings.Brightness, ref y, delegate(int v) { settings.Brightness = v; }, true);

        Label hint = new Label();
        hint.Text = "Zavri toto okno = farby sa vrátia naspäť.";
        hint.AutoSize = true;
        hint.ForeColor = Color.FromArgb(170, 180, 190);
        hint.Location = new Point(16, y + 4);
        Controls.Add(hint);

        // Hry (aj Valorant vo fullscreene) obcas gamma resetnu -> kazde 2 s ju nastavime znova.
        reapply.Interval = 2000;
        reapply.Tick += delegate { Apply(); };

        Load += delegate { Apply(); reapply.Start(); };
        FormClosing += delegate { RestoreOnce(); };
        Application.ApplicationExit += delegate { RestoreOnce(); };
        Microsoft.Win32.SystemEvents.SessionEnding += delegate { RestoreOnce(); };
        AppDomain.CurrentDomain.UnhandledException += delegate { RestoreOnce(); };
    }

    void AddSlider(string name, int min, int max, int value, ref int y, Action<int> set, bool enabled)
    {
        Label label = new Label();
        label.AutoSize = true;
        label.Location = new Point(16, y);
        Controls.Add(label);

        TrackBar bar = new TrackBar();
        bar.Minimum = min; bar.Maximum = max;
        bar.Value = Math.Max(min, Math.Min(max, value));
        bar.TickStyle = TickStyle.None;
        bar.Location = new Point(170, y - 4);
        bar.Size = new Size(195, 30);
        bar.Enabled = enabled;
        Controls.Add(bar);

        label.Text = name + ": " + bar.Value;
        bar.ValueChanged += delegate
        {
            set(bar.Value);
            label.Text = name + ": " + bar.Value;
            settings.Save();
            Apply();
        };
        y += 46;
    }

    void Apply()
    {
        string msg = "";
        if (NvVibrance.Available)
        {
            try { NvVibrance.SetPercent(settings.Vibrance); msg += "Vibrance OK. "; }
            catch (Exception) { msg += "Vibrance zlyhala. "; }
        }
        else msg += "NVIDIA nenájdená – vibrance nejde (len kontrast/gamma). ";

        ushort[] ramp = Gamma.Build(settings.Contrast / 100.0, settings.Gamma / 100.0, settings.Brightness / 100.0);
        bool ok = true;
        foreach (string m in Gamma.Monitors()) ok &= Gamma.Set(m, ramp);
        msg += ok ? "Kontrast/gamma OK." : "Windows odmietol takú silnú krivku – zníž kontrast/gammu.";
        status.Text = msg;
    }

    void RestoreOnce()
    {
        if (restored) return;
        restored = true;
        reapply.Stop();
        Backup.Restore();
    }
}

public static class App
{
    public static void Run()
    {
        NvVibrance.Init();

        // Ak minule program spadol, najprv vratime povodne farby z disku.
        if (Backup.LoadLeftover()) Backup.Restore();
        Backup.Capture();

        Application.EnableVisualStyles();
        try { Application.Run(new ColorGradeForm()); }
        finally { Backup.Restore(); }
    }
}
'@

Add-Type -TypeDefinition $source -ReferencedAssemblies System.Windows.Forms, System.Drawing
[App]::Run()
