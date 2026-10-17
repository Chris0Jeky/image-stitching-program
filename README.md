# image-stitching-program

A small Python image-composition utility.

Only the first four photos in filename order are decoded. Selected photos above
40 million pixels and collage canvases above 20 million pixels are rejected
before decoding or canvas allocation, respectively.

Camera EXIF orientation is applied before scaling and aligning photo heights.

## License

`compose.py` and the owner-authored documentation are licensed under GNU GPL
version 3 only (`GPL-3.0-only`). See `LICENSE` and `LICENSING.md`.

The images in `images/**` and `output/**`, plus `logo.jpg`, are excluded because
their provenance and redistribution rights have not been established. See
`THIRD_PARTY_NOTICES.md`.
 
