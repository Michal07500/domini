# Valorant Color Grade
# Kym je toto okno otvorene -> farby su "hernne" (vibrance + kontrast).
# Ked okno zavries -> vsetko sa vrati presne tak, ako to bolo predtym.
#
# Spustaj cez "Spustit ColorGrade.bat" (dvojklik).
# Automaticky pri Valorante: "Zapnut automaticky.bat".

param([switch]$Auto)   # -Auto = cakaj na Valorant v liste pri hodinach

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
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int OutputIdFn(IntPtr handle, out uint outputId);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int DisplayNameFn(IntPtr handle, [MarshalAs(UnmanagedType.LPArray, SizeConst = 64)] byte[] name);

    [StructLayout(LayoutKind.Sequential)]
    struct DvcInfo { public uint version; public int current; public int min; public int max; }

    static EnumDisplayFn enumDisplay;
    static GetDvcFn getDvc;
    static SetDvcFn setDvc;
    static readonly List<IntPtr> displays = new List<IntPtr>();
    static readonly List<uint> outputs = new List<uint>();
    static readonly List<string> names = new List<string>();

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
            OutputIdFn outputId = Fn<OutputIdFn>(0xD995937E);
            DisplayNameFn displayName = Fn<DisplayNameFn>(0x22A78B05);
            for (int i = 0; i < 16; i++)
            {
                IntPtr h;
                if (enumDisplay(i, out h) != 0) break;
                // Kazdy monitor ma na karte vlastny vystup - vibrance musi ist presne nan.
                uint id = 0;
                if (outputId == null || outputId(h, out id) != 0) id = 0;
                byte[] buf = new byte[64];
                string name = "NVIDIA displej " + (i + 1);
                if (displayName != null && displayName(h, buf) == 0) name = Encoding.ASCII.GetString(buf).TrimEnd('\0');
                displays.Add(h);
                outputs.Add(id);
                names.Add(name);
            }
            Available = displays.Count > 0;
        }
        catch (Exception) { Available = false; } // nie je NVIDIA karta / driver
    }

    static DvcInfo Info(IntPtr h)
    {
        DvcInfo info = new DvcInfo();
        info.version = (uint)Marshal.SizeOf(typeof(DvcInfo)) | (1u << 16);
        getDvc(h, outputs[displays.IndexOf(h)], ref info);
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
        for (int i = 0; i < displays.Count && i < levels.Length; i++) setDvc(displays[i], outputs[i], levels[i]);
    }

    // percent = to iste cislo ako "Digital Vibrance" v NVIDIA Control Panel (50 = default, 100 = max)
    // vrati pre kazdy monitor "nazov: OK / chyba"
    public static List<string> SetPercent(int percent)
    {
        List<string> result = new List<string>();
        for (int i = 0; i < displays.Count; i++)
        {
            DvcInfo info = Info(displays[i]);
            int level = (int)Math.Round((Math.Max(50, Math.Min(100, percent)) - 50) / 50.0 * info.max);
            int err = setDvc(displays[i], outputs[i], level);
            result.Add(names[i] + ": vibrance " + (err == 0 ? "OK" : "CHYBA " + err));
        }
        return result;
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

// ---------------------------------------------------------------- Zapnutie / vypnutie farieb
public static class Grader
{
    public static Settings Settings = Settings.Load();
    public static bool Active { get; private set; }

    public static void Start()
    {
        if (Active) return;
        Backup.Capture();          // zapamatat si povodne farby
        Active = true;
    }

    public static void Stop()
    {
        if (!Active) return;
        Active = false;
        Backup.Restore();          // vratit povodne farby
    }

    // nastavi farby, vrati stav pre kazdy monitor
    public static string Apply()
    {
        if (!Active) return "";
        List<string> lines = new List<string>();
        if (NvVibrance.Available)
        {
            try { lines.AddRange(NvVibrance.SetPercent(Settings.Vibrance)); }
            catch (Exception e) { lines.Add("Vibrance zlyhala: " + e.Message); }
        }
        else lines.Add("NVIDIA nenájdená – vibrance nejde.");

        ushort[] ramp = Gamma.Build(Settings.Contrast / 100.0, Settings.Gamma / 100.0, Settings.Brightness / 100.0);
        foreach (string m in Gamma.Monitors())
            lines.Add(m + ": kontrast " + (Gamma.Set(m, ramp) ? "OK" : "ODMIETNUTÝ"));
        return string.Join("\n", lines.ToArray());
    }
}

// ---------------------------------------------------------------- Okno s posuvnikmi
public class ColorGradeForm : Form
{
    Label status = new Label();
    Timer refresh = new Timer();

    public ColorGradeForm(bool auto)
    {
        Settings settings = Grader.Settings;
        Text = "Valorant Color Grade";
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(15, 25, 35);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10f);
        ClientSize = new Size(380, 370);

        Label title = new Label();
        title.Text = "COLOR GRADE: ZAPNUTÝ";
        title.Font = new Font("Segoe UI", 15f, FontStyle.Bold);
        title.ForeColor = Color.FromArgb(255, 70, 85);
        title.AutoSize = true;
        title.Location = new Point(16, 12);
        Controls.Add(title);

        status.AutoSize = false;
        status.Size = new Size(350, 80);
        status.Location = new Point(16, 46);
        status.ForeColor = Color.FromArgb(170, 180, 190);
        Controls.Add(status);

        int y = 132;
        AddSlider("Vibrance (NVIDIA %)", 50, 100, settings.Vibrance, ref y, delegate(int v) { settings.Vibrance = v; }, NvVibrance.Available);
        AddSlider("Kontrast %", 100, 140, settings.Contrast, ref y, delegate(int v) { settings.Contrast = v; }, true);
        AddSlider("Gamma (x100)", 70, 130, settings.Gamma, ref y, delegate(int v) { settings.Gamma = v; }, true);
        AddSlider("Jas", -10, 10, settings.Brightness, ref y, delegate(int v) { settings.Brightness = v; }, true);

        Label hint = new Label();
        hint.Text = auto
            ? "Náhľad. Po zavretí okna sa farby zapnú, len keď beží Valorant."
            : "Zavri toto okno = farby sa vrátia naspäť.";
        hint.AutoSize = false;
        hint.Size = new Size(350, 40);
        hint.ForeColor = Color.FromArgb(170, 180, 190);
        hint.Location = new Point(16, y + 4);
        Controls.Add(hint);

        // Hry (aj Valorant vo fullscreene) obcas gamma resetnu -> kazde 2 s ju nastavime znova.
        refresh.Interval = 2000;
        refresh.Tick += delegate { status.Text = Grader.Apply(); };
        Load += delegate { Grader.Start(); status.Text = Grader.Apply(); refresh.Start(); };
        FormClosed += delegate { refresh.Stop(); };
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
            Grader.Settings.Save();
            status.Text = Grader.Apply();
        };
        y += 46;
    }
}

// ---------------------------------------------------------------- Automaticky rezim (ikonka v liste pri hodinach)
public class AutoWatcher : ApplicationContext
{
    const string GameProcess = "VALORANT-Win64-Shipping"; // samotna hra (nie launcher)

    NotifyIcon icon = new NotifyIcon();
    Timer check = new Timer();
    ColorGradeForm settingsForm;

    public AutoWatcher()
    {
        ContextMenuStrip menu = new ContextMenuStrip();
        menu.Items.Add("Nastavenia farieb", null, delegate { OpenSettings(); });
        menu.Items.Add("Ukončiť", null, delegate { ExitThread(); });

        icon.Icon = SystemIcons.Application;
        icon.ContextMenuStrip = menu;
        icon.DoubleClick += delegate { OpenSettings(); };
        icon.Visible = true;

        check.Interval = 2000;
        check.Tick += delegate { Tick(); };
        check.Start();
        Tick();
    }

    static bool GameRunning()
    {
        System.Diagnostics.Process[] p = System.Diagnostics.Process.GetProcessesByName(GameProcess);
        foreach (System.Diagnostics.Process x in p) x.Dispose();
        return p.Length > 0;
    }

    void Tick()
    {
        bool game = GameRunning();
        bool wanted = game || settingsForm != null;
        if (wanted && !Grader.Active) Grader.Start();
        if (!wanted && Grader.Active) Grader.Stop();
        if (Grader.Active) Grader.Apply();
        icon.Text = game ? "Color Grade: ZAPNUTÝ (Valorant beží)" : "Color Grade: čaká na Valorant";
    }

    void OpenSettings()
    {
        if (settingsForm != null) { settingsForm.Activate(); return; }
        settingsForm = new ColorGradeForm(true);
        settingsForm.FormClosed += delegate { settingsForm = null; Tick(); };
        settingsForm.Show();
    }

    protected override void ExitThreadCore()
    {
        check.Stop();
        if (settingsForm != null) settingsForm.Close();
        icon.Visible = false;
        icon.Dispose();
        Grader.Stop();
        base.ExitThreadCore();
    }
}

public static class App
{
    public static void Run(bool auto)
    {
        bool first;
        System.Threading.Mutex single = new System.Threading.Mutex(true, "ValorantColorGrade_SingleInstance", out first);
        if (!first)
        {
            MessageBox.Show("Color Grade už beží (pozri ikonku v lište pri hodinách).", "Valorant Color Grade");
            return;
        }

        NvVibrance.Init();

        // Ak minule program spadol, najprv vratime povodne farby z disku.
        if (Backup.LoadLeftover()) Backup.Restore();

        Application.ApplicationExit += delegate { Grader.Stop(); };
        Microsoft.Win32.SystemEvents.SessionEnding += delegate { Grader.Stop(); };
        AppDomain.CurrentDomain.UnhandledException += delegate { Grader.Stop(); };

        Application.EnableVisualStyles();
        try
        {
            if (auto) Application.Run(new AutoWatcher());
            else Application.Run(new ColorGradeForm(false));
        }
        finally
        {
            Grader.Stop();
            GC.KeepAlive(single);
        }
    }
}
'@

Add-Type -TypeDefinition $source -ReferencedAssemblies System.Windows.Forms, System.Drawing
[App]::Run($Auto.IsPresent)
