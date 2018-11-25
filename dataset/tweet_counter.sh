#!/bin/bash
clear
sep=15
arrayFormat="%${sep}s | %${sep}s | %${sep}s | %${sep}s | %${sep}s |  %${sep}s"
sizeregex="s/^([[:alnum:].,]+).*/\\1/"

function users_cmd() {
	path="tweets/${1}/users.csv"
	if [[ ! -f ${path} ]]; then
		echo "- / -"
	else
		echo "$(($(cat ${path} | wc -l) - 1)) / $(cat ${1}.txt | wc -l)"
	fi
}
function tweets_cmd() {
	path="tweets/${1}/tweets.csv"
	if [[ ! -f ${path} ]]; then
		echo "-"
	else
		echo $(($(cat ${path} | wc -l) - 1))
	fi
}

function tweetsSize_cmd() {
	path="tweets/${1}/tweets.csv"
	if [[ ! -f ${path} ]]; then
		echo "-"
	else
		echo $(du -ha ${path} | sed -E ${sizeregex})
	fi
}

function usersSize_cmd() {
	path="tweets/${1}/users.csv"
	if [[ ! -f ${path} ]]; then
		echo '-'
	else
		echo $(du -ha ${path} | sed -E ${sizeregex})
	fi
}

function print_info() {
	printf "${arrayFormat}$2" ${1} "$(users_cmd $1)" $(tweets_cmd $1) $(usersSize_cmd $1) $(tweetsSize_cmd $1)
}

function print_array_begin() {
	printf "${arrayFormat}\n" "Category" "Users" "Tweets" "Users filesize" "Tweets filesize"
	for i in {1..89}; do
		printf '%c' '_'
	done
	printf '\n'
}

if [[ $1 == '-s' ]]; then
	print_array_begin 15
	for group in athletes celebrities actors musicians politicians; do
		print_info $group '\n'
	done
	exit
else
	groupname=$1
fi

while true; do
	if [[ ! (-f tweets/${groupname}/users.csv && -f tweets/${groupname}/tweets.csv) ]]; then
		printf "%s\r" "No needed files for ${1}"
		continue
	else
		break
	fi
done

print_array_begin 15
while true; do
	print_info $groupname '\r'
	sleep 0.5
done
