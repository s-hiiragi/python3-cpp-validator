#include <stdio.h>

int main()
{
	int x = 0;

	{
		//!unused x
		printf("%d\n", x);  //=> error
	}
	printf("%d\n", x);  //=> ok

	return 0;
}

