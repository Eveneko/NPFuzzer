#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>

int vuln(char *str)
{
    int len = strlen(str);
    if (str[0] == 'F' && len == 6)
    {
        raise(SIGSEGV);
        //如果输入的字符串的首字符为F并且长度为6，则异常退出
    }
    else
    {
        printf("it is good!\n");
    }
    return 0;
}

int main(int argc, char *argv[])
{
    char buf[100] = {0};
    gets(buf);
    printf(buf); //存在格式化字符串漏洞
    puts("");
    vuln(buf);

    return 0;
}