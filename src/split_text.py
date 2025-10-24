import sys
import regex

def separate_words(input_file, output_file):
    with open(input_file, 'r') as file:
        text = file.read()
    
    #words = regex.findall(r'\b\w+\b', text)
    words = text.split()
    
    with open(output_file, 'w') as file:
        for word in words:
            file.write(f"{word}\n")

def main():
    if len(sys.argv) != 3:
        print("Usage: python split_text.py <input_file> <output_file>")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    # input_file = 'data/test.txt'
    # output_file = 'data/split.txt'
    
    separate_words(input_file, output_file)

if __name__ == "__main__":
    main()