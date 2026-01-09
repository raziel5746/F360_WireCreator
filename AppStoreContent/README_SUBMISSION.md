# Wire Creator - App Store Submission Checklist

## ✅ What's Ready

### Bundle Structure (`WireCreator.bundle/`)
```
WireCreator.bundle/
├── PackageContents.xml          ← Package manifest for Autodesk
├── Contents/
│   ├── WireCreator.py          ← Main add-in code
│   ├── WireCreator.manifest    ← Fusion 360 add-in manifest
│   ├── help.html               ← Quick start guide (included with download)
│   └── Resources/              ← Place your icons here (see below)
```

### Marketing Content (`AppStoreContent/`)
| File | Purpose | Action Needed |
|------|---------|---------------|
| `short_description.txt` | Brief tagline for listings | Copy text to form |
| `full_description.md` | Detailed feature description | Copy text to form |
| `privacy_policy.md` | Required privacy policy | Host online & link |
| `support_info.md` | Support contact details | Reference for form |

---

## ⚠️ You Need To Update

### 1. Replace Placeholder Info
Search for `your.email@example.com` and `Your Name` in these files:
- `WireCreator.bundle/PackageContents.xml`
- `WireCreator.bundle/Contents/WireCreator.manifest`
- `AppStoreContent/privacy_policy.md`
- `AppStoreContent/support_info.md`
- `AppStoreContent/full_description.md`

### 2. App Icon
The App Store requires a **120x120 pixel** icon.
- Place your icon in: `WireCreator.bundle/Contents/Resources/`
- Recommended sizes: 16x16, 32x32, 64x64, 120x120 (PNG format)
- You already have: `Wire Creator Logo.png` - resize as needed

### 3. Host Privacy Policy Online
You need to host `privacy_policy.md` at a public URL and link to it in:
- The App Store submission form
- Optionally in the add-in's help dialog

---

## 📤 Submission Steps

1. **Complete Publisher Profile** (you're doing this now)
2. **Zip the bundle**: Create `WireCreator.zip` containing `WireCreator.bundle/`
3. **Fill out submission form** with content from `AppStoreContent/`
4. **Upload** zip file, logo, and screenshots
5. **Submit** and wait for reviewer contact (24-48 hours)

### Create the Zip File
Run this command in PowerShell:
```powershell
Compress-Archive -Path "WireCreator.bundle" -DestinationPath "WireCreator.zip"
```

---

*Good luck with your submission! 🚀*
