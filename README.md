# bsz-gimp-plugins
### Plugins for GIMP 2.99+
## Installation
Either
 - Download the release and unpack it into your already existing plugins folder
 - Or, for cleanliness, unpack the release to its own folder and add that folder as a plug-in directory in Gimp's folder settings

## Building
Needs the bszgw.py file from https://github.com/Beinsezii/BSZGW at the root. Will be bundled with releases.

Compiling any shared libraries needs rustc and the rustup toolchain for the target platform. Small build scripts provided for Linux.

## Current Plugins

### Dual Bloom
Provides light and dark bloom using thresholds. Based on my own custom bloom methods.

<img width=400 src="./bsz-dualbloom/during.png" />
<table class="img-compare">
  <tr>
    <th><img width=250 src="./bsz-dualbloom/before.png" alt="Before" /></th>
    <th><img width=250 src="./bsz-dualbloom/after.png" alt="After" /></th>
  </tr>
  <tr>
    <td>Before</td>
    <td>After</td>
  </tr>
</table>

### Dual Bloom 2
Produces both a light and dark bloom, based on gimp/gegl's existing bloom.

<img width=400 src="./bsz-dualbloom2/during.png" />
<table class="img-compare">
  <tr>
    <th><img width=250 src="./bsz-dualbloom2/before.png" alt="Before" /></th>
    <th><img width=250 src="./bsz-dualbloom2/after.png" alt="After" /></th>
  </tr>
  <tr>
    <td>Before</td>
    <td>After</td>
  </tr>
</table>

### Filmic Chroma
Reduces/increases chroma based on intensity. Inspired by Blender's new 'Filmic' tonemapper.

<img width=300 src="./bsz-filmic-chroma/during.png" />
<table class="img-compare">
  <tr>
    <th>Before</th>
    <th>After</th>
  </tr>
  <tr>
    <td><img width=250 src="./bsz-filmic-chroma/before.png" alt="Before" /></td>
    <td><img width=250 src="./bsz-filmic-chroma/after.png" alt="After" /></td>
  </tr>
  <tr>
    <td><img height=300 src="./bsz-filmic-chroma/before2.png" alt="Before" /></td>
    <td><img height=300 src="./bsz-filmic-chroma/after2.png" alt="After" /></td>
  </tr>
</table>

### Lightgrain
LCH Noise masked to Lightness

<img width=300 src="./bsz-lightgrain/during.png" />
<table class="img-compare">
  <tr>
    <th><img width=250 src="./bsz-lightgrain/before.png" alt="Before" /></th>
    <th><img width=250 src="./bsz-lightgrain/after.png" alt="After" /></th>
  </tr>
  <tr>
    <td>Before</td>
    <td>After</td>
  </tr>
</table>

### Pixel Math
Enter custom Python algorithms for pixel math.

<img width=300 src="./bsz-pixel-math/during.png" />

### Pixel Math 2
Enter basic operations to perform pixel math. More limited, but processes well over 20x faster than Pixel Math in the worst scenarios.

<img width=300 src="./bsz-pixel-math-2/during.png" />


## bsz_gimp_lib
Shared library for plugins. Notably contains a *complete plugin auto-builder*. Similar to the old python-fu, but (imo) significantly more customizable at a mild complexity cost. Features include
 - Semi-live previews using gegl buffers.
 - UI that isn't just a bunch of widgets smashed into a column (but it can be if that's what you want)
   - Chains
   - Logarithmic scales courtesy of BSZGW
 - Extensible using the Param abstract class. Plugins can make their own widgets/parameters.
   - Has built-in Param derivatives for most common data input fields.
 - Somewhat documented mostly in nice words.
Check out bsz-dualbloom.py for a decent GEGL filter example, and bsz-filmic-chroma.py for a decent custom math/FFI example. This obviously can't cover every plugin use scenario, but I'd say covering 95% of use cases is good enough. 

Other non-plugin-builder bits include:
 - Premade dictionary of Gegl compositors
   - Ripped from the gegl site's html.
   - Only includes operations that use pads input, aux, output.
 - PDB quick function. WIP, many datatypes not supported.
