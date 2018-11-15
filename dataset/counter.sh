#!/bin/bash
while true; do
	if [[ ! (-f tweets/${1}/users.csv && -f tweets/${1}/tweets.csv) ]]; then
		printf "%s\r" "No needed files for ${1}"
		continue
	else
        break
    fi
done

separatorSize=15
arrayFormat="%${separatorSize}s | %${separatorSize}s | %${separatorSize}s | %${separatorSize}s | %${separatorSize}s |"
printf "${arrayFormat}\n" "Category" "Users" "Tweets" "Users filesize" "Tweets filesize"

for i in {1..89}; do
	printf '%c' '_'
done
printf '\n'

while true; do
	users="$(cat tweets/${1}/users.csv | wc -l)/$(cat ${1}.txt | wc -l)"
	tweets=$(cat tweets/${1}/tweets.csv | wc -l)
	tweetsSize=$(du -ha tweets/${1}/tweets.csv | sed -E "s/^([[:alnum:].,]+).*/\\1/")
	usersSize=$(du -ha tweets/${1}/users.csv | sed -E "s/^([[:alnum:].,]+).*/\\1/")
	printf "${arrayFormat}\r" ${1} ${users} ${tweets} ${usersSize} ${tweetsSize}
done
