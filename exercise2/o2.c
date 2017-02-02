#include <pthread.h>
#include <stdio.h>

static int i = 0;

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

// Note the return type: void*
void* thread_1(){
    int j;
    for (j = 0; j < 1000000; j++){
        pthread_mutex_lock(&mutex);
    	i ++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

void* thread_2(){
    int j;
    for (j = 0; j < 1000000; j++){
        pthread_mutex_lock(&mutex);
    	i --;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}



int main(){
    pthread_t t1;
    pthread_t t2;
    
    pthread_create(&t1, NULL, thread_1, NULL);
    pthread_create(&t2, NULL, thread_2, NULL);
    // Arguments to a thread would be passed here ---------^
    
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("%d\n",i);
    return 0;
    
}