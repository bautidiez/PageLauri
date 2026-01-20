// Script to optimize images for production
// Run with: node optimize-images.js

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// Configuration
const IMAGE_DIRS = [
    path.join(__dirname, 'public', 'assets'),
    path.join(__dirname, 'src', 'assets')
];

const OUTPUT_DIR = path.join(__dirname, 'public', 'assets', 'optimized');
const QUALITY = 80; // JPEG quality (1-100)
const WEBP_QUALITY = 80; // WebP quality (1-100)

async function ensureDirectoryExists(directory) {
    if (!fs.existsSync(directory)) {
        fs.mkdirSync(directory, { recursive: true });
    }
}

async function optimizeImage(inputPath, outputPath, filename) {
    const ext = path.extname(filename).toLowerCase();

    try {
        const image = sharp(inputPath);
        const metadata = await image.metadata();

        console.log(`Processing: ${filename} (${metadata.width}x${metadata.height})`);

        // Optimize based on file type
        if (ext === '.jpg' || ext === '.jpeg') {
            await image
                .jpeg({ quality: QUALITY, progressive: true })
                .toFile(outputPath);

            // Also create WebP version
            const webpPath = outputPath.replace(/\\.jpe?g$/, '.webp');
            await sharp(inputPath)
                .webp({ quality: WEBP_QUALITY })
                .toFile(webpPath);

            console.log(`  ✓ Optimized JPEG and created WebP`);
        } else if (ext === '.png') {
            await image
                .png({ compressionLevel: 9, progressive: true })
                .toFile(outputPath);

            // Also create WebP version
            const webpPath = outputPath.replace(/\\.png$/, '.webp');
            await sharp(inputPath)
                .webp({ quality: WEBP_QUALITY, lossless: false })
                .toFile(webpPath);

            console.log(`  ✓ Optimized PNG and created WebP`);
        } else if (ext === '.webp') {
            await image
                .webp({ quality: WEBP_QUALITY })
                .toFile(outputPath);

            console.log(`  ✓ Optimized WebP`);
        } else {
            // Copy other files as-is
            fs.copyFileSync(inputPath, outputPath);
            console.log(`  ℹ Copied ${filename} (unsupported format for optimization)`);
        }

        // Compare file sizes
        const originalSize = fs.statSync(inputPath).size;
        const optimizedSize = fs.statSync(outputPath).size;
        const savings = ((originalSize - optimizedSize) / originalSize * 100).toFixed(1);

        console.log(`  Original: ${(originalSize / 1024).toFixed(1)}KB → Optimized: ${(optimizedSize / 1024).toFixed(1)}KB (${savings}% savings)`);

    } catch (error) {
        console.error(`  ✗ Error processing ${filename}:`, error.message);
    }
}

async function processDirectory(directory) {
    if (!fs.existsSync(directory)) {
        console.log(`Directory not found: ${directory}`);
        return;
    }

    const files = fs.readdirSync(directory);

    for (const file of files) {
        const fullPath = path.join(directory, file);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
            // Skip node_modules and other system directories
            if (file !== 'node_modules' && file !== 'optimized' && !file.startsWith('.')) {
                await processDirectory(fullPath);
            }
        } else if (stat.isFile()) {
            const ext = path.extname(file).toLowerCase();
            const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];

            if (imageExtensions.includes(ext)) {
                const relativePath = path.relative(path.join(__dirname, 'public', 'assets'), fullPath);
                const outputPath = path.join(OUTPUT_DIR, relativePath);
                const outputDir = path.dirname(outputPath);

                await ensureDirectoryExists(outputDir);
                await optimizeImage(fullPath, outputPath, file);
            }
        }
    }
}

async function main() {
    console.log('🖼️  Image Optimization Script\n');
    console.log('This will optimize all images and create WebP versions\n');

    // Ensure output directory exists
    await ensureDirectoryExists(OUTPUT_DIR);

    // Process each directory
    for (const dir of IMAGE_DIRS) {
        console.log(`\n📁 Processing directory: ${dir}\n`);
        await processDirectory(dir);
    }

    console.log('\n✅ Image optimization complete!');
    console.log(`\nOptimized images saved to: ${OUTPUT_DIR}`);
    console.log('\nNext steps:');
    console.log('1. Review the optimized images');
    console.log('2. Replace original images with optimized versions if satisfied');
    console.log('3. Update image references to use WebP with fallbacks');
}

// Check if sharp is installed
try {
    require.resolve('sharp');
    main().catch(console.error);
} catch (e) {
    console.error('❌ Error: sharp package is not installed');
    console.log('\nPlease install sharp by running:');
    console.log('  npm install --save-dev sharp');
    process.exit(1);
}
