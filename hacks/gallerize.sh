#!/usr/bin/env bash

debug() {
    test -z "${DEBUG}" || >&2 echo ">> ${@}"
}
export -f debug

err() {
    >&2 echo "!! ${@}"
}
export -f err

export PHOTO_SIZE="1600x1200"
export PHOTO_Q="98"
export THUMB_SIZE="640x480"
export THUMB_Q="80"
CMD="${1}"; shift
SRC="${1}"; shift
export DEST="${1}"

if [ -z "${SRC}" ] || [ -z "${DEST}" ]; then
    err "need to specify source and destination as arguments"
    exit 1
fi

image() {
    local img_path b_name f_name f_ext
    img_path="${1}"

    test -f "${img_path}" || { err "no such file: ${img_path}"; exit 2; }

    b_name=$(basename "${img_path}" | tr '[:upper:]' '[:lower:]')
    debug "processing ${b_name}"
    f_name="${b_name%.*}"
    f_ext="${b_name##*.}"

    # full image
    convert "${img_path}"        \
        -resize "${PHOTO_SIZE}>" \
        -quality "${PHOTO_Q}"    \
        "${DEST}/${f_name}.${f_ext}"

    # thumb
    convert "${img_path}"        \
        -resize "${THUMB_SIZE}>" \
        -quality "${THUMB_Q}"    \
        "${DEST}/${f_name}.thumb.${f_ext}"
}
export -f image

dir() {
    local source_dir
    source_dir="${1}"
    test -d "${source_dir}" || { err "no such dir: ${source_dir}"; exit 2; }

    find -L "${source_dir}" -mindepth 1 -print0 \
        | parallel --null -j 4 image
}

# dispatch
mkdir -p "${DEST}"
"$CMD" "${SRC}"
