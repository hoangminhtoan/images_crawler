if [ "$#" -ne 1 ]; then
	echo "Usage: bash show_number_of_files.sh [directory/to/folder]"
	exit 0
fi

echo "Moving to $1"
cd "$1"

du -a | cut -d/ -f2 | sort | uniq -c | sort -nr

echo "More detail"
find . -type d -print0 | while read -d '' -r dir; do
    files=("$dir"/*)
    printf "%5d files in directory %s\n" "${#files[@]}" "$dir"
done


