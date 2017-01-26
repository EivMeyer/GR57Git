#include <pthread.h>
#include <stdio.h>

static int i = 0;

// Note the return type: void*
void* thread_1(){
    for (int j = 0; j < 1000000; j++){
    	i ++;
    }
    return NULL;
}

void* thread_2(){
    for (int j = 0; j < 1000000; j++){
    	i --;
    }
    return NULL;
}

int main(){
    pthread_t t1;
    pthread_create(&t1, NULL, thread_1, NULL);

    pthread_t t2;
    pthread_create(&t2, NULL, thread_2, NULL);
    // Arguments to a thread would be passed here ---------^
    
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("%d",i);
    return 0;
    
}