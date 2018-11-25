#!/bin/bash

clear
sep=15
arrayFormat="%${sep}s | %${sep}s | %${sep}s | %${sep}s"
sizeregex="s/^([[:alnum:].,]+).*/\\1/"

if [[ $# < 1 ]]; then
	echo "Pass group name"
	exit
fi

groupname=$1

function print_array_begin() {
	printf "${arrayFormat}\n" "Category" "Username" "Followers" "Filesize"
	for i in {1..89}; do
		printf '%c' '_'
	done
	printf '\n'
}

function filesize() {
	# $1 - username
	path="followers/$groupname/$1/usernames.csv"
	if [[ ! -f $path ]]; then
		echo -
	else
		echo $(du -ha $path | sed -E $sizeregex)
	fi
}

function followers() {
	# $1 - username
	path="followers/$groupname/$1/usernames.csv"
	if [[ ! -f $path ]]; then
		echo -
	else
		echo $(($(cat $path | wc -l) - 1))
	fi
}

function print_info() {
	# $1 - username
	printf "$arrayFormat\n" $groupname $1 "$(followers $1)" "$(filesize $1)"
}

function find_users() {
	# $1 - groupname
	find followers/$groupname/* -type d | sed -E "s/followers\/$groupname\/(.*)/\\1/" | tr '\n' ' '
}

while true; do
    clear && printf '\e[3J'
	print_array_begin
	users=$(find_users)
	for user in $users; do
		print_info $user
	done
	sleep 1
done
