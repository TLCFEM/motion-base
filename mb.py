import sys

from mb import run_app

if __name__ == '__main__':
    arg_dict = {}
    index = 1
    while index < len(sys.argv):
        if sys.argv[index].startswith('w'):
            arg_dict['workers'] = int(sys.argv[index + 1])
            index += 2
        elif sys.argv[index].startswith('h'):
            arg_dict['host'] = sys.argv[index + 1]
            index += 2
        else:
            index += 1

    print(f'Run the app with the following arguments: {arg_dict}')
    run_app(**arg_dict)
