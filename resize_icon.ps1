# Generate Android app icons
Add-Type -AssemblyName System.Drawing

$sourcePath = "d:\biancheng\yueduqi\legado_reader\app_icon.png"

# Define sizes
$sizes = @{
    "mipmap-mdpi" = 48
    "mipmap-hdpi" = 72
    "mipmap-xhdpi" = 96
    "mipmap-xxhdpi" = 144
    "mipmap-xxxhdpi" = 192
}

foreach ($folder in $sizes.Keys) {
    $size = $sizes[$folder]
    $targetDir = "d:\biancheng\yueduqi\legado_reader\android\app\src\main\res\$folder"
    
    # Load source image
    $image = [System.Drawing.Image]::FromFile($sourcePath)
    
    # Create new image
    $newImage = New-Object System.Drawing.Bitmap($size, $size)
    $graphics = [System.Drawing.Graphics]::FromImage($newImage)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.DrawImage($image, 0, 0, $size, $size)
    
    # Save ic_launcher.png
    $newImage.Save("$targetDir\ic_launcher.png", [System.Drawing.Imaging.ImageFormat]::Png)
    
    # Save ic_launcher_round.png
    $newImage.Save("$targetDir\ic_launcher_round.png", [System.Drawing.Imaging.ImageFormat]::Png)
    
    # Save ic_launcher_foreground.png
    $newImage.Save("$targetDir\ic_launcher_foreground.png", [System.Drawing.Imaging.ImageFormat]::Png)
    
    $graphics.Dispose()
    $newImage.Dispose()
    $image.Dispose()
    
    Write-Host "Generated $folder (${size}x${size})"
}

Write-Host "All icons generated successfully!"
