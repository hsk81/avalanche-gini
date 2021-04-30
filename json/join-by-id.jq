def hash_join(a1; a2; field):
  # hash phase:
  (reduce a1[] as $o ({};  . + { ($o | field): $o } )) as $h1
  | (reduce a2[] as $o ({};  . + { ($o | field): $o } )) as $h2
  # join phase:
  | reduce ($h1|keys[]) as $key
      ([]; if $h2|has($key) then . + [ $h1[$key] + $h2[$key] ] else . end) ;

hash_join($f1; $f2; .id)[]
